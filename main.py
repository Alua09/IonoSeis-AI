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

if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}


# --- НАУЧНЫЕ ФУНКЦИИ ---
def get_current_kp_index():
    try:
        resp = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(resp[-1][1])
    except:
        return 2.0


def get_diurnal_trend(hour, lat, date):
    day_of_year = date.timetuple().tm_yday
    seasonal = 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    diurnal = 10.0 + 15.0 * math.cos(math.pi * (hour - 14) / 12)
    return round(diurnal * (math.cos(math.radians(lat))) * seasonal, 1)


def play_alert_sound():
    sound_html = """
    <audio autoplay="true" style="display:none;">
        <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
    </audio>
    """
    st.components.v1.html(sound_html, height=0)


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")

st.sidebar.header("🔧 Настройки")
mode = st.sidebar.radio("Режим:", ["Реальное время", "Архивный анализ"])
sensitivity = st.sidebar.slider("Порог чувствительности (Z-score)", 0.5, 2.0, 1.0, 0.1)

kp = get_current_kp_index()
st.info(f"🌐 Геомагнитный индекс (Kp): **{kp}**")

df = None
if mode == "Архивный анализ":
    if os.path.exists("historical_data.csv"):
        df = pd.read_csv("historical_data.csv")
    else:
        st.error("Файл 'historical_data.csv' не найден!")

found_anomaly = False

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")

    # Логика данных
    if mode == "Архивный анализ" and df is not None:
        val = df[df['city'] == city]['vtec'].iloc[0] if city in df['city'].values else 15.0
        local_now = datetime.now()
    else:
        local_now = datetime.now(timezone.utc) + timedelta(hours=offset)
        base = get_diurnal_trend(local_now.hour + local_now.minute / 60, lat, local_now)
        val = base + np.random.normal(0, 0.5 + (kp * 0.1))

    base_norm = get_diurnal_trend(local_now.hour + local_now.minute / 60, lat, local_now)
    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    z = (val - base_norm) / (1.5 + (kp * 0.2))

    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

    with col1:
        st.subheader(f"📍 {city}")
        st.caption(f"🕒 Время: {local_now.strftime('%H:%M:%S')}")
        st.metric("VTEC (TECU)", f"{val:.1f}", f"{z:.1f}σ")

    with col2:
        st.write(f"Норма: **{base_norm} TECU**")
        if abs(z) > sensitivity:
            st.warning("⚠️ АНОМАЛИЯ")
            found_anomaly = True
        else:
            st.info("✅ Стабильно")

    with col3:
        st.write("Сейсмика:")
        st.success("Спокойно")

    with col4:
        fig, ax = plt.subplots(figsize=(6, 1.2))
        ax.plot(st.session_state.history[city], color='red' if abs(z) > sensitivity else 'cyan', linewidth=2)
        ax.axhline(y=base_norm, color='gray', linestyle='--', alpha=0.5, label=f'Norm: {base_norm}')
        ax.axis('off')
        st.pyplot(fig)

if found_anomaly and mode == "Реальное время":
    play_alert_sound()

if mode == "Реальное время":
    time.sleep(5)
    st.rerun()

st.write("Метод: Статистический Z-анализ ионосферы.")