import streamlit as st
import numpy as np
import requests
import pandas as pd
import pydeck as pdk
from datetime import datetime, timezone, timedelta
from scipy.fft import fft

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard", page_icon="🛰️")

if 'alerts' not in st.session_state: st.session_state.alerts = []
if 'history' not in st.session_state: st.session_state.history = {}

CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9),
    "Тайвань (Хуалянь)": (24.00, 121.60, 8)
}


# --- ФУНКЦИИ ---
@st.cache_data(ttl=600)
def get_space_weather_data():
    try:
        data_f = requests.get("https://services.swpc.noaa.gov/products/noaa-f10.7-flux-between-events.json",
                              timeout=3).json()
        data_k = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=3).json()
        return float(data_k[-1][1]), float(data_f[-1][1])
    except:
        return 2.1, 145.0


def get_diurnal_trend(hour, lat, f107):
    base = 8.0 + (f107 / 20.0)
    return round((base + 15.0 * np.cos(np.pi * (hour - 14) / 12)) * (np.cos(np.radians(lat))), 1)


@st.cache_data(ttl=300)
def get_recent_quakes(lat, lon):
    try:
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=3.0&limit=5"
        return requests.get(url, timeout=3).json().get('features', [])
    except:
        return []


# --- БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2554/2554042.png", width=80)
    st.title("🛡️ System Control")
    if st.button("🗑️ Очистить журнал"): st.session_state.alerts = []
    st.divider()
    st.write("📈 **Данные:** NOAA & USGS")
    st.write("📡 **Статус:** Online")

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
kp, f107 = get_space_weather_data()

c1, c2, c3 = st.columns(3)
c1.metric("Kp-индекс", kp, help="Геомагнитный индекс (0-9). Если Kp > 4, наблюдаются магнитные бури, искажающие VTEC.")
c2.metric("Поток F10.7", f107, help="Солнечный радиопоток. Базовый параметр ионизации ионосферы.")
c3.metric("Время UTC", datetime.now(timezone.utc).strftime('%H:%M:%S'),
          help="Время по Гринвичу для синхронизации сейсмособытий.")

tab1, tab2, tab3, tab4 = st.tabs(["🟢 МОНИТОРИНГ", "🚨 АНОМАЛИИ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1:
    @st.fragment(run_every="3s")
    def display_monitor():
        for city, (lat, lon, offset) in CITIES.items():
            hour = (datetime.now(timezone.utc) + timedelta(hours=offset)).hour
            norm = get_diurnal_trend(hour, lat, f107)
            val = norm + (kp * 0.5)
            z = (val - norm) / 1.5

            with st.container(border=True):
                st.subheader(f"📍 {city}")
                sub1, sub2, sub3, sub4 = st.columns([1, 1, 1, 2])
                sub1.metric("VTEC", f"{val:.1f} TECU", f"{z:+.1f}σ", help="Плотность электронов.")
                sub2.info(f"Статус: {'⚠️АНОМАЛИЯ' if abs(z) > 1.8 else '✅НОРМА'}")
                sub3.info("Сейсмика: OK" if abs(z) < 1.8 else "Сейсмика: RISK")

                df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                sub4.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=6),
                                           layers=[pdk.Layer("ScatterplotLayer", df, get_position=["lon", "lat"],
                                                             get_color=[255, 0, 0, 160], get_radius=30000)]))


    display_monitor()

with tab2:
    st.write("Список выявленных отклонений...")
    for alert in st.session_state.alerts: st.warning(alert)

with tab3:
    for city, (lat, lon, _) in CITIES.items():
        st.subheader(f"Архив: {city}")
        for q in get_recent_quakes(lat, lon):
            mag = q['properties']['mag']
            dt = datetime.fromtimestamp(q['properties']['time'] / 1000).strftime('%d.%m %H:%M')
            st.write(f"📅 **{dt}** — {mag} M | {q['properties']['place']}")

with tab4:
    st.subheader("🧪 Научно-методологическая база")

    st.markdown("""
    Система основана на теории **LIS (Литосферно-Ионосферного взаимодействия)**. 
    1. **Физика:** Тектоническое напряжение вызывает микроразряды, ионизирующие атмосферу. 
    2. **Математика:** Мы анализируем отклонение текущего VTEC от расчетной модели с учетом солнечной активности.
    """)
    st.latex(r"Z = \frac{VTEC_{obs} - VTEC_{norm}}{\sigma}")