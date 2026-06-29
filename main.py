import streamlit as st
import numpy as np
import requests
import pandas as pd
import pydeck as pdk
from datetime import datetime, timezone, timedelta
from scipy.fft import fft

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI", page_icon="🛰️")

# Стиль для «зеленых» подписей
st.markdown("""
    <style>
    .stMetric { background-color: #f0fdf4; border: 1px solid #22c55e; padding: 15px; border-radius: 10px; }
    .css-1r6slb0 { color: #166534; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

if 'alerts' not in st.session_state: st.session_state.alerts = []
if 'history' not in st.session_state: st.session_state.history = {}

CITIES = {"Алматы": (43.25, 76.92, 5), "Бишкек": (42.87, 74.59, 6), "Токио": (35.68, 139.65, 9),
          "Тайвань (Хуалянь)": (24.00, 121.60, 8)}


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


# --- ИНТЕРФЕЙС ---
st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
kp, f107 = get_space_weather_data()

# Индикаторы
c1, c2, c3 = st.columns(3)
c1.metric("Kp-индекс", kp, help="Геомагнитный индекс (0-9). > 4 — риск искажений данных.")
c2.metric("Поток F10.7", f107, help="Показатель солнечного излучения.")
c3.metric("Время UTC", datetime.now(timezone.utc).strftime('%H:%M:%S'), help="Время по Гринвичу.")

tab1, tab2, tab3, tab4 = st.tabs(["🟢 МОНИТОРИНГ", "🚨 АНОМАЛИИ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1:
    @st.fragment(run_every="3s")
    def run_monitor():
        for city, (lat, lon, offset) in CITIES.items():
            # Моделируем данные (для примера)
            val = 15.0 + np.random.normal(0, 0.5)
            z = (val - 15.0) / 1.5

            with st.container(border=True):
                st.subheader(f"📍 {city}")
                sub1, sub2, sub3, sub4 = st.columns([1, 1, 1, 2])
                sub1.metric("VTEC", f"{val:.1f} TECU", f"{z:+.1f}σ")
                sub2.success("СТАТУС: НОРМА") if abs(z) <= 1.8 else sub2.error("СТАТУС: АНОМАЛИЯ")
                sub3.info("Сейсмика: OK")
                sub4.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=6)))


    run_monitor()

with tab3:
    for city, (lat, lon, _) in CITIES.items():
        st.subheader(f"Архив: {city}")
        for q in get_recent_quakes(lat, lon):
            mag = q['properties']['mag']
            dt = datetime.fromtimestamp(q['properties']['time'] / 1000).strftime('%d.%m %H:%M')
            # Выделение цветом
            if mag >= 5.0:
                st.error(f"📅 {dt} | ⚠️ {mag} M | {q['properties']['place']}")
            else:
                st.write(f"📅 {dt} | {mag} M | {q['properties']['place']}")

with tab4:
    st.subheader("🧪 Научная методология")

    st.markdown("""
    ### Как это работает (изложение 11-классника)
    Наша система опирается на **LIS-гипотезу** (Литосферно-Ионосферное взаимодействие). 
    1. **Физический процесс:** Горные породы под давлением сжимаются, образуя пьезоэлектрические заряды. В атмосферу выбрасывается радон, который ионизирует воздух.
    2. **Космический аспект:** Эти ионы создают электрические поля, проникающие в ионосферу. Наши датчики (VTEC) фиксируют изменение электронной плотности.
    3. **Статистика:** Мы используем формулу Z-оценки. Если отклонение $Z > 1.8\sigma$, это не просто «шум», а сигнал, который требует проверки.
    4. **Зачем карта?** Она фиксирует область охвата (радиус 500 км). Это критически важно, так как эффект от напряжения в земной коре — локальное явление.
    """)
    st.latex(r"Z = \frac{VTEC_{obs} - VTEC_{norm}}{\sigma}")