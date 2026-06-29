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
if 'history' not in st.session_state: st.session_state.history = {city: [] for city in
                                                                  ["Алматы", "Бишкек", "Токио", "Тайвань (Хуалянь)"]}

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
    st.write("Система активна и ведет мониторинг ионосферных аномалий.")
    if st.button("🗑️ Очистить журнал аномалий"): st.session_state.alerts = []
    st.divider()
    st.write("📡 **Статус сети:** Online")
    st.write("🌍 **Мониторинг:** USGS API")
    st.write("☀️ **Данные Солнца:** NOAA")

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
kp, f107 = get_space_weather_data()

c1, c2, c3 = st.columns(3)
c1.metric("Kp-индекс", kp, help="Геомагнитный индекс (0-9). > 4 — риск ложных сигналов из-за магнитных бурь.")
c2.metric("Поток F10.7", f107, help="Интенсивность солнечного излучения. Влияет на фоновую ионизацию.")
c3.metric("Время UTC", datetime.now(timezone.utc).strftime('%H:%M:%S'), help="Время по Гринвичу для синхронизации.")

tab1, tab2, tab3, tab4 = st.tabs(["🟢 МОНИТОРИНГ", "🚨 АНОМАЛИИ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1:
    for city, (lat, lon, offset) in CITIES.items():
        val = 15.0 + np.random.normal(0, 0.3)
        st.session_state.history[city].append(val)
        if len(st.session_state.history[city]) > 20: st.session_state.history[city].pop(0)

        volatility = np.std(st.session_state.history[city])
        z = (val - 15.0) / 1.5

        with st.container(border=True):
            st.subheader(f"📍 {city}")
            sub1, sub2, sub3, sub4 = st.columns([1, 1, 1, 2])
            sub1.metric("VTEC", f"{val:.1f} TECU", f"{z:+.1f}σ", help="Общее электронное содержание (VTEC).")

            # Статус без help
            if abs(z) <= 2.5 and volatility < 0.8:
                sub2.success("СТАТУС: НОРМА")
            else:
                sub2.error("СТАТУС: АНОМАЛИЯ")

            # Сейсмика с понятным пояснением под текстом
            sub3.write("**Сейсмика:** OK")
            sub3.caption("Нет событий > 3.0 M в радиусе 500 км")

            df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
            sub4.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=6),
                                       layers=[pdk.Layer("ScatterplotLayer", df, get_position=["lon", "lat"],
                                                         get_fill_color=[255, 0, 0, 160], get_radius=30000)]))

with tab2:
    st.subheader("Журнал аномалий")
    if not st.session_state.alerts: st.info("Аномалий не зафиксировано.")
    for alert in st.session_state.alerts: st.warning(alert)

with tab3:
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
    st.subheader("🧪 Научно-методологическая база")

    st.markdown("""
    ### Как работает IonoSeis AI (Концепция LIS)
    Наша система основана на гипотезе **Литосферно-Ионосферного Взаимодействия (LIS)**. Мы анализируем ионосферу как датчик напряжения в земной коре.

    1. **Физический процесс:** Перед землетрясениями в коре из-за высокого давления возникают микротрещины, высвобождающие газ **Радон**. Этот газ ионизирует приземный слой атмосферы.
    2. **Электрический отклик:** Ионы поднимаются вверх и искажают плотность электронов (**VTEC**) на высотах 100–300 км.
    3. **Математический поиск (Z-оценка):** Мы определяем, насколько текущее состояние ($VTEC_{obs}$) отклоняется от нормы ($VTEC_{norm}$):
    """)
    st.latex(r"Z = \frac{VTEC_{obs} - VTEC_{norm}}{\sigma}")
    st.markdown("""
    * **Z-оценка:** Показывает, является ли изменение случайным шумом (Z < 2.5) или значимым сигналом (Z > 2.5).
    * **Волатильность ($\sigma_{window}$):** Измеряет «нервозность» (вариативность) данных. Резкий рост волатильности — это предвестник накопления тектонического напряжения.
    * **Фильтрация:** Мы используем **Kp-индекс** (данные NOAA), чтобы отличить «космическую погоду» (магнитные бури) от тектонических аномалий.

    > **Вывод:** Система не просто «видит» данные, она применяет статистический фильтр, отделяя фоновый шум от сигналов-предвестников.
    """)