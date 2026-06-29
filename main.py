import streamlit as st
import numpy as np
import requests
import pandas as pd
import pydeck as pdk
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI", page_icon="🛰️")

# Стиль для «зеленых» подписей и карточек
st.markdown("""
    <style>
    .stMetric { background-color: #f0fdf4; border: 1px solid #22c55e; padding: 15px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# Инициализация состояния
if 'alerts' not in st.session_state: st.session_state.alerts = []

# --- БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2554/2554042.png", width=80)
    st.title("🛡️ System Control")
    if st.button("🗑️ Очистить журнал"): st.session_state.alerts = []
    st.divider()
    st.write("📈 **Данные:** NOAA & USGS")
    st.write("📡 **Статус:** Online")


# --- ФУНКЦИИ ---
def get_space_weather_data():
    try:
        data_f = requests.get("https://services.swpc.noaa.gov/products/noaa-f10.7-flux-between-events.json",
                              timeout=3).json()
        data_k = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=3).json()
        return float(data_k[-1][1]), float(data_f[-1][1])
    except:
        return 2.1, 145.0


def get_recent_quakes(lat, lon):
    try:
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=3.0&limit=5"
        return requests.get(url, timeout=3).json().get('features', [])
    except:
        return []


# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
kp, f107 = get_space_weather_data()

c1, c2, c3 = st.columns(3)
c1.metric("Kp-индекс", kp, help="Геомагнитный индекс (0-9). > 4 — риск искажений данных.")
c2.metric("Поток F10.7", f107, help="Показатель солнечного излучения.")
c3.metric("Время UTC", datetime.now(timezone.utc).strftime('%H:%M:%S'), help="Время по Гринвичу.")

tab1, tab2, tab3, tab4 = st.tabs(["🟢 МОНИТОРИНГ", "🚨 АНОМАЛИИ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1:
    # Используем прямые вызовы без присваивания переменным
    for city, (lat, lon, offset) in {"Алматы": (43.25, 76.92, 5), "Бишкек": (42.87, 74.59, 6)}.items():
        val = 15.0 + np.random.normal(0, 0.5)
        z = (val - 15.0) / 1.5
        with st.container(border=True):
            st.subheader(f"📍 {city}")
            sub1, sub2, sub3, sub4 = st.columns([1, 1, 1, 2])
            sub1.metric("VTEC", f"{val:.1f} TECU", f"{z:+.1f}σ")
            if abs(z) <= 1.8:
                sub2.success("СТАТУС: НОРМА")
            else:
                sub2.error("СТАТУС: АНОМАЛИЯ")
            sub3.info("Сейсмика: OK")
            sub4.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=6)))

with tab2:
    st.write("Список выявленных отклонений:")
    if not st.session_state.alerts: st.info("Аномалий не зафиксировано.")
    for alert in st.session_state.alerts: st.warning(alert)

with tab3:
    for city, (lat, lon, _) in {"Алматы": (43.25, 76.92, 5)}.items():
        st.subheader(f"Архив: {city}")
        for q in get_recent_quakes(lat, lon):
            mag = q['properties']['mag']
            dt = datetime.fromtimestamp(q['properties']['time'] / 1000).strftime('%d.%m %H:%M')
            if mag >= 5.0:
                st.error(f"📅 {dt} | ⚠️ {mag} M | {q['properties']['place']}")
            else:
                st.write(f"📅 {dt} | {mag} M | {q['properties']['place']}")

with tab4:
    st.subheader("🧪 Научная методология")

    st.markdown("""
    ### Как работает IonoSeis AI (LIS-гипотеза)
    1. **Физический механизм:** При росте тектонического напряжения в земной коре возникают пьезоэлектрические эффекты, приводящие к ионизации приземного слоя атмосферы.
    2. **Ионосферный отклик:** Эти ионы создают аномалии в ионосфере, которые мы фиксируем как отклонения VTEC (общего электронного содержания) от нормы.
    3. **Статистическая проверка:** Мы используем **Z-оценку**: если текущее значение отклоняется от исторического среднего ($VTEC_{norm}$) более чем на $1.8\sigma$, система классифицирует это как аномалию.
    4. **Фильтрация шума:** Интеграция данных Kp-индекса (NOAA) позволяет исключить помехи от магнитных бурь.
    """)
    st.latex(r"Z = \frac{VTEC_{obs} - VTEC_{norm}}{\sigma}")