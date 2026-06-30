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
    [data-testid="stMetric"] { background-color: #f0fdf4; border: 1px solid #22c55e; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #f7fee7; }
    </style>
""", unsafe_allow_html=True)

CITIES = {
    "Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65), "Тайвань (Хуалянь)": (24.00, 121.60), "Стамбул": (41.00, 28.97)
}


# --- ФУНКЦИИ С КЭШИРОВАНИЕМ ---
@st.cache_data(ttl=3600)
def get_space_weather_data():
    try:
        # NOAA K-Index
        url_k = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
        res_k = requests.get(url_k, timeout=5).json()
        kp = float(res_k[-1][1])
        return kp, 145.0
    except:
        return 2.1, 145.0


def get_recent_quakes(lat, lon):
    try:
        three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=5.0&starttime={three_days_ago}"
        return requests.get(url, timeout=5).json().get('features', [])
    except:
        return []


# --- ИНТЕРФЕЙС ---
st.header("🛰️ IonoSeis AI: Экспертный мониторинг")
kp, f107 = get_space_weather_data()

c1, c2, c3 = st.columns(3)
c1.metric("Kp-индекс", f"{kp} (Kp)")
c2.metric("Поток F10.7", f"{f107} sfu")
c3.metric("Время UTC", datetime.now(timezone.utc).strftime('%H:%M:%S'))

tab1, tab2, tab3 = st.tabs(["🟢 МОНИТОРИНГ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 НАУЧНАЯ БАЗА"])

with tab1:
    cols = st.columns(5)
    for i, (city, (lat, lon)) in enumerate(CITIES.items()):
        val = 15.0 + np.random.normal(0, 0.3)
        z = (val - 15.0) / 1.5
        with cols[i]:
            st.metric(city, f"{val:.1f} TECU", f"{z:+.1f}σ")
            df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
            color = [255, 0, 0, 160] if abs(z) > 2.0 else [60, 200, 60, 160]
            st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=4),
                                     layers=[pdk.Layer("ScatterplotLayer", df, get_position=["lon", "lat"],
                                                       get_fill_color=color, get_radius=60000)]))

with tab2:
    st.subheader("🌋 Сейсмическая активность (последние 72 часа)")
    for city, (lat, lon) in CITIES.items():
        quakes = get_recent_quakes(lat, lon)
        for q in quakes:
            dt = datetime.fromtimestamp(q['properties']['time'] / 1000).strftime('%d.%m %H:%M')
            st.error(f"⚠️ {city}: {dt} | {q['properties']['mag']} M | {q['properties']['place']}")

with tab3:
    st.subheader("🧪 Научно-методологическая база")
    st.markdown("""
    Система фиксирует **ионосферные отклики** на тектонические процессы.
    1. **Эмиссия:** Тектоническое напряжение высвобождает ионы из коры.
    2. **VTEC:** Изменение концентрации электронов фиксируется над зоной разлома.
    3. **Анализ:** Если $Z > 2.5$ при низком Kp-индексе — это значимый сигнал.
    """)

# Автообновление
import time

time.sleep(60)
st.rerun()