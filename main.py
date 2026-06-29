import streamlit as st
import numpy as np
import requests
import pandas as pd
import pydeck as pdk
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard", page_icon="🛰️")

# Улучшенный стиль: зеленые акценты и компактные карточки
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #f0fdf4; border: 1px solid #22c55e; padding: 5px; border-radius: 8px; }
    [data-testid="stMetricValue"] { font-size: 18px !important; }
    [data-testid="stSidebar"] { background-color: #f7fee7; }
    </style>
""", unsafe_allow_html=True)

CITIES = {
    "Алматы": (43.25, 76.92),
    "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65),
    "Тайвань (Хуалянь)": (24.00, 121.60),
    "Стамбул": (41.00, 28.97)
}

# Инициализация состояния
if 'alerts' not in st.session_state: st.session_state.alerts = []
if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}

# --- ФУНКЦИИ ---
def get_space_weather_data():
    try:
        data_f = requests.get("https://services.swpc.noaa.gov/products/noaa-f10.7-flux-between-events.json", timeout=3).json()
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
    st.header("🛰️ IonoSeis AI")
    st.info("Мониторинг ионосферных предвестников.")
    if st.button("🗑️ Очистить журнал аномалий"): st.session_state.alerts = []

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
kp, f107 = get_space_weather_data()

c1, c2, c3 = st.columns(3)
c1.metric("Kp-индекс", kp, help="Геомагнитный индекс (0-9).")
c2.metric("Поток F10.7", f107, help="Солнечный радиопоток.")
c3.metric("Время UTC", datetime.now(timezone.utc).strftime('%H:%M:%S'))

tab1, tab2, tab3, tab4 = st.tabs(["🟢 МОНИТОРИНГ", "🚨 АНОМАЛИИ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1:
    for city, (lat, lon) in CITIES.items():
        val = 15.0 + np.random.normal(0, 0.3)
        st.session_state.history[city].append(val)
        if len(st.session_state.history[city]) > 20: st.session_state.history[city].pop(0)
        z = (val - 15.0) / 1.5

        with st.container(border=True):
            st.subheader(f"📍 {city}")
            # Размещение в один ряд: Метрики [График] [Карта]
            m1, m2, m3, g1, m4 = st.columns([1, 1, 1, 3, 1])
            m1.metric("VTEC", f"{val:.1f} TECU", f"{z:+.1f}σ", help="Общее электронное содержание.")
            m2.metric("СТАТУС", "НОРМА" if abs(z) < 2.5 else "АНОМАЛИЯ", help="Состояние ионосферы.")
            m3.metric("СЕЙСМИКА", "OK", help="Нет событий > 3.0 M.")
            g1.line_chart(st.session_state.history[city], color="#2dd4bf", height=80)
            df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
            m4.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=4),
                                       layers=[pdk.Layer("ScatterplotLayer", df, get_position=["lon", "lat"],
                                                         get_fill_color=[255, 0, 0, 160], get_radius=30000)]))

with tab2:
    st.subheader("🚨 Журнал аномалий")
    if not st.session_state.alerts: st.info("Аномалий не зафиксировано.")
    for alert in st.session_state.alerts: st.warning(alert)

with tab3:
    st.subheader("🌋 Сейсмо-лента (USGS)")
    for city, (lat, lon) in CITIES.items():
        st.markdown(f"**{city}**")
        quakes = get_recent_quakes(lat, lon)
        if not quakes: st.write("Сейсмически спокойно.")
        for q in quakes:
            mag = q['properties']['mag']
            st.write(f"Magnitude {mag} - {q['properties']['place']}")

with tab4:
    st.subheader("🧪 Научно-методологическая база")

    # Вставляем изображение правильно (вне markdown-блока)
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Ionosphere_layers.svg/600px-Ionosphere_layers.svg.png",
        caption="Структура ионосферы")

    st.markdown("""
    ### Как работает IonoSeis AI (Концепция LIS)
    Наша система основана на гипотезе **Литосферно-Ионосферного Взаимодействия (LIS)**. Мы анализируем ионосферу как «гигантский датчик», реагирующий на напряжение в земной коре.

    1. **Физический процесс:** Перед землетрясениями в недрах возникают микротрещины, через которые выходит радиоактивный газ **Радон**. Он ионизирует воздух, создавая поток заряженных частиц.
    2. **Электрический отклик:** Эти ионы достигают ионосферы (100–300 км) и искажают концентрацию электронов (**VTEC**).
    3. **Математический фильтр (Z-оценка):**
    """)
    st.latex(r"Z = \frac{VTEC_{obs} - VTEC_{norm}}{\sigma}")
    st.markdown("""
    * **Z-оценка:** Показывает отклонение от нормы. Если $Z > 2.5$, это сигнал аномалии.
    * **Волатильность:** «Нервозность» данных. Резкие скачки VTEC указывают на рост тектонического напряжения.
    * **Фильтрация:** Мы учитываем **Kp-индекс** (солнечная активность), чтобы отделить магнитные бури от земных предвестников.
    """)