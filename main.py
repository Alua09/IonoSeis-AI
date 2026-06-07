import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import time
import math
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard")

# (Широта, Долгота, Смещение UTC)
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
    # Учет сезонности (равноденствия)
    seasonal = 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    # Суточный ход: пик около 14:00 местного времени
    diurnal = 10.0 + 15.0 * math.cos(math.pi * (total_hours - 14) / 12)

    # Модель VTEC
    vtec = diurnal * (math.cos(math.radians(lat))) * seasonal
    # Модель сигмы (зависит от ионизации)
    sigma = 0.5 + (0.05 * abs(vtec) / 10.0)
    return round(vtec, 2), round(sigma, 3)


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Мониторинг ионосферы")

kp = get_real_kp_index()
st.sidebar.info(f"🌐 Kp-индекс: **{kp}**")
sensitivity = st.sidebar.slider("Порог чувствительности (Z-score)", 0.5, 2.0, 1.0, 0.1)

# ОСНОВНОЙ ЦИКЛ
for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")

    # 1. Расчет локального времени
    now_utc = datetime.now(timezone.utc)
    local_now = now_utc + timedelta(hours=offset)
    total_hours = local_now.hour + local_now.minute / 60 + local_now.second / 3600

    # 2. Расчет уникальных параметров
    vtec_model, sigma = get_ionospheric_params(total_hours, lat, local_now.timetuple().tm_yday)

    # 3. Значение VTEC (реальное + влияние Kp)
    val = vtec_model + (kp * 0.4)

    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    # 4. Расчет Z-score
    z = (val - vtec_model) / (sigma + 0.1)

    # ВЫВОД ДАННЫХ
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.subheader(f"📍 {city}")
        st.write(f"🕒 Время: **{local_now.strftime('%H:%M:%S')}**")
        st.metric("VTEC", f"{val:.2f}", f"{z:.2f}σ")
    with col2:
        st.write(f"$\sigma$ (отклонение): **{sigma}**")
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