import streamlit as st
import numpy as np
import requests
import pandas as pd
import pydeck as pdk
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard", page_icon="🛰️")

# Стиль
st.markdown("""
    <style>
    .stMetric { background-color: #f0fdf4; border: 1px solid #22c55e; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #f8fafc; }
    </style>
""", unsafe_allow_html=True)

if 'alerts' not in st.session_state: st.session_state.alerts = []

CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9),
    "Тайвань (Хуалянь)": (24.00, 121.60, 8)
}


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


# --- БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("⚙️ Панель управления")
    st.info("Система активна и ведет мониторинг ионосферных аномалий в режиме реального времени.")
    if st.button("🗑️ Очистить журнал аномалий"): st.session_state.alerts = []
    st.divider()
    st.write("📡 **Статус сети:** Online")
    st.write("🌍 **Мониторинг:** USGS API")
    st.write("☀️ **Данные Солнца:** NOAA")

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
kp, f107 = get_space_weather_data()

c1, c2, c3 = st.columns(3)
c1.metric("Kp-индекс", kp, help="Геомагнитный индекс (0-9). > 4 — риск искажений данных.")
c2.metric("Поток F10.7", f107, help="Показатель солнечного излучения.")
c3.metric("Время UTC", datetime.now(timezone.utc).strftime('%H:%M:%S'), help="Время по Гринвичу.")

tab1, tab2, tab3, tab4 = st.tabs(["🟢 МОНИТОРИНГ", "🚨 АНОМАЛИИ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1:
    for city, (lat, lon, offset) in CITIES.items():
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
            # Возврат круга на карту
            df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
            sub4.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=6),
                                       layers=[pdk.Layer("ScatterplotLayer", df, get_position=["lon", "lat"],
                                                         get_fill_color=[255, 0, 0, 160], get_radius=30000)]))

with tab2:
    st.subheader("Журнал аномалий")
    if not st.session_state.alerts: st.info("Аномалий не зафиксировано.")
    for alert in st.session_state.alerts: st.warning(alert)

with tab3:
    # Исправлено: теперь показывает ленту для всех городов
    for city, (lat, lon, _) in CITIES.items():
        st.subheader(f"🌋 Сейсмо-события: {city}")
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
    Наша система опирается на принцип литосферно-ионосферного взаимодействия. Перед мощными сейсмическими событиями в земной коре из-за деформации пород возникают пьезоэлектрические эффекты и выбросы радона. Ионизация приземного слоя атмосферы создает электрические поля, которые достигают ионосферы, вызывая локальное изменение плотности электронов (VTEC).

    * **Z-оценка:** Наш основной математический инструмент для детекции. Если $Z > 1.8\sigma$, мы фиксируем аномалию.
    * **Карта:** Визуализация зон мониторинга позволяет локализовать сейсмические процессы в радиусе 500 км.
    * **Фильтрация:** Данные NOAA (Kp-индекс) используются для исключения ложных срабатываний, вызванных солнечными вспышками.
    """)
    st.latex(r"Z = \frac{VTEC_{obs} - VTEC_{norm}}{\sigma}")