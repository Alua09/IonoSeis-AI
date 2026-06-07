import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import time
import math
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Monitoring")

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
    try:
        # Увеличили радиус для более "редких" событий, чтобы не спамило
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=5.5&limit=1"
        data = requests.get(url, timeout=5).json()
        if data['features']:
            return data['features'][0]['properties']['mag']
        return 0
    except:
        return 0


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Мониторинг")
kp = get_real_kp_index()

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")

    # 1. Индивидуальный расчет для каждого города
    local_now = datetime.now(timezone.utc) + timedelta(hours=offset)
    total_hours = local_now.hour + local_now.minute / 60

    # Модель VTEC с поправкой на широту (lat)
    # Используем cos(lat), чтобы города на разных широтах имели разную "базу"
    vtec_base = (10.0 + 15.0 * math.cos(math.pi * (total_hours - 14) / 12)) * math.cos(math.radians(lat))

    # 2. Уникальная сигма для каждого города (зависит от широты)
    sigma = 0.3 + (0.02 * lat / 10.0)

    # 3. Получаем реальную сейсмику
    mag = get_seismic_activity(lat, lon)

    # VTEC = База + влияние Kp + сейсмический скачок
    val = vtec_base + (kp * 0.3) + (mag * 5.0 if mag > 0 else np.random.normal(0, 0.05))

    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    z = (val - vtec_base) / sigma

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.subheader(f"📍 {city}")
        st.metric("VTEC", f"{val:.2f}", f"{z:.2f}σ")
    with col2:
        if mag > 0:
            st.warning(f"⚠️ ЗЕМЛЕТРЯСЕНИЕ M{mag}!")
        elif abs(z) > 1.8:  # Порог чувствительности
            st.warning("⚠️ АНОМАЛИЯ ИОНОСФЕРЫ")
        else:
            st.success("✅ Стабильно")
    with col3:
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='red' if abs(z) > 1.8 else 'cyan')
        ax.axis('off')
        st.pyplot(fig)

time.sleep(5)
st.rerun()