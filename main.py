import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import math
import time
import pandas as pd
import os
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard")

CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}

# Инициализация состояния
if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}


# --- ФУНКЦИИ ---
def get_current_kp_index():
    try:
        # Получаем данные о геомагнитной активности
        resp = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(resp[-1][1])
    except:
        return 2.0


def get_diurnal_trend(hour, lat, date):
    # Моделирование суточного хода VTEC
    day_of_year = date.timetuple().tm_yday
    seasonal = 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    diurnal = 10.0 + 15.0 * math.cos(math.pi * (hour - 14) / 12)
    return round(diurnal * (math.cos(math.radians(lat))) * seasonal, 1)


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")

st.sidebar.header("🔧 Настройки")
mode = st.sidebar.radio("Режим:", ["Реальное время", "Архивный анализ"])
sensitivity = st.sidebar.slider("Порог чувствительности (Z-score)", 0.5, 2.0, 1.0, 0.1)

kp = get_current_kp_index()
st.info(f"🌐 Текущий геомагнитный индекс (Kp): **{kp}**")

# ОСНОВНОЙ ЦИКЛ
for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")

    # Расчет данных
    local_now = datetime.now(timezone.utc) + timedelta(hours=offset)
    base_norm = get_diurnal_trend(local_now.hour + local_now.minute / 60, lat, local_now)
    # Генерация данных с учетом Kp-индекса (шума)
    val = base_norm + np.random.normal(0, 0.5 + (kp * 0.1))

    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    z = (val - base_norm) / (1.5 + (kp * 0.2))

    # Визуальное отображение
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        st.subheader(f"📍 {city}")
        st.metric("VTEC (TECU)", f"{val:.1f}", f"{z:.1f}σ")

    with col2:
        if abs(z) > sensitivity:
            st.error(f"🚨 АНОМАЛИЯ!")
            st.balloons()  # Эффект привлечения внимания
        else:
            st.success("✅ Стабильно")

    with col3:
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='red' if abs(z) > sensitivity else 'cyan', linewidth=2)
        ax.axis('off')
        st.pyplot(fig)

if mode == "Реальное время":
    time.sleep(3)
    st.rerun()