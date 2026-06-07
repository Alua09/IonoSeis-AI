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
    """Рассчитывает VTEC и его стандартное отклонение (sigma)"""
    # Сезонный коэффициент (макс. в равноденствие)
    seasonal = 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    # Суточный ход: максимум в 14:00 местного времени
    diurnal = 10.0 + 15.0 * math.cos(math.pi * (total_hours - 14) / 12)

    vtec = diurnal * (math.cos(math.radians(lat))) * seasonal

    # Сигма зависит от интенсивности ионизации (чем больше VTEC, тем больше шум)
    sigma = 0.5 + (0.1 * vtec / 10.0)
    return vtec, sigma


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Анализ ионосферы в реальном времени")
kp = get_real_kp_index()
st.info(f"🌐 Текущий планетарный Kp-индекс NOAA: **{kp}**")

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")
    now = datetime.now(timezone.utc) + timedelta(hours=offset)
    total_hours = now.hour + now.minute / 60 + now.second / 3600

    # Получаем индивидуальные параметры для города
    vtec_model, sigma = get_ionospheric_params(total_hours, lat, now.timetuple().tm_yday)

    # Добавляем влияние геомагнитной бури (Kp)
    val = vtec_model + (kp * 0.8)

    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    # Z-score теперь учитывает динамическую сигму города
    z = (val - vtec_model) / (sigma + (kp * 0.1))

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.subheader(f"📍 {city}")
        st.write(f"🕒 Время: {now.strftime('%H:%M:%S')}")
        st.metric("VTEC", f"{val:.2f}", f"{z:.2f}σ")
    with col2:
        st.write(f"Стандартное отклонение ($\sigma$): **{sigma:.2f}**")
        if abs(z) > 1.5:
            st.warning("⚠️ АНОМАЛИЯ")
        else:
            st.success("✅ Стабильно")
    with col3:
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='red' if abs(z) > 1.5 else 'cyan')
        ax.axis('off')
        st.pyplot(fig)

time.sleep(1)
st.rerun()