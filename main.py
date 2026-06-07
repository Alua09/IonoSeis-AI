import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import time
import math
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard")

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


def get_ionospheric_params(total_hours, lat, day_of_year):
    seasonal = 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    diurnal = 10.0 + 15.0 * math.cos(math.pi * (total_hours - 14) / 12)
    vtec = diurnal * (math.cos(math.radians(lat))) * seasonal
    sigma = 0.5 + (0.05 * abs(vtec) / 10.0)
    return round(vtec, 2), round(sigma, 3)


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Мониторинг ионосферы")
kp = get_real_kp_index()
st.sidebar.info(f"🌐 Kp-индекс: **{kp}**")
sensitivity = st.sidebar.slider("Порог чувствительности (Z-score)", 0.5, 2.0, 1.0, 0.1)

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")

    local_now = datetime.now(timezone.utc) + timedelta(hours=offset)
    total_hours = local_now.hour + local_now.minute / 60 + local_now.second / 3600

    vtec_model, sigma = get_ionospheric_params(total_hours, lat, local_now.timetuple().tm_yday)

    # Добавляем случайную турбулентность, зависящую от Kp
    fluctuation = np.random.normal(0, 0.05 + (kp * 0.02))
    val = vtec_model + (kp * 0.4) + fluctuation

    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    z = (val - vtec_model) / (sigma + 0.1)

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.subheader(f"📍 {city}")
        st.write(f"🕒 Время: **{local_now.strftime('%H:%M:%S')}**")
        st.metric("VTEC", f"{val:.2f}", f"{z:.2f}σ")
    with col2:
        st.write(f"$\sigma$: **{sigma}**")
        if abs(z) > sensitivity:
            st.warning("⚠️ АНОМАЛИЯ")
        else:
            st.success("✅ Стабильно")
    with col3:
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='red' if abs(z) > sensitivity else 'cyan', linewidth=2)
        ax.axis('off')
        st.pyplot(fig)

time.sleep(1)
st.rerun()