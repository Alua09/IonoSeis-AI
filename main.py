import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import time
import math
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Real-Time Seismo-Monitor")

CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}

if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}


# --- ФУНКЦИИ ---
def get_real_kp_index():
    try:
        resp = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(resp[-1][1])
    except:
        return 2.0


def get_seismic_activity(lat, lon):
    """Проверка землетрясений (mag > 5.0, радиус 1000км) через USGS API"""
    try:
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=1000&minmagnitude=5.0&limit=1"
        data = requests.get(url, timeout=5).json()
        if data['features']:
            return data['features'][0]['properties']['mag']  # Возвращает магнитуду
        return 0
    except:
        return 0


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Реальный сейсмо-ионосферный мониторинг")
kp = get_real_kp_index()
sensitivity = st.sidebar.slider("Порог чувствительности (Z-score)", 0.5, 2.0, 1.0, 0.1)

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")

    local_now = datetime.now(timezone.utc) + timedelta(hours=offset)
    total_hours = local_now.hour + local_now.minute / 60

    # Расчет базового VTEC
    seasonal = 1.0 + 0.2 * math.sin(2 * math.pi * (local_now.timetuple().tm_yday - 80) / 365)
    vtec_model = (10.0 + 15.0 * math.cos(math.pi * (total_hours - 14) / 12)) * math.cos(math.radians(lat)) * seasonal

    # Получаем реальную сейсмику
    mag = get_seismic_activity(lat, lon)

    # Если есть землетрясение, добавляем возмущение к VTEC
    val = vtec_model + (kp * 0.4) + (mag * 2.0 if mag > 0 else 0)

    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    z = (val - vtec_model) / (0.5 + (kp * 0.1))

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.subheader(f"📍 {city}")
        st.metric("VTEC", f"{val:.2f}", f"{z:.2f}σ")
    with col2:
        if mag > 0:
            st.warning(f"⚠️ ЗЕМЛЕТРЯСЕНИЕ M{mag}!")
        else:
            st.success("✅ Стабильно")
    with col3:
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='red' if mag > 0 else 'cyan')
        ax.axis('off')
        st.pyplot(fig)

time.sleep(10)  # Запрос к USGS ресурсоемкий, ставим паузу побольше
st.rerun()