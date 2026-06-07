import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import time
import base64
import math
from gtts import gTTS
from datetime import datetime, timezone, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Real-Time Expert")

CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}

if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}
if 'audio_activated' not in st.session_state:
    st.session_state.audio_activated = False


def get_real_kp_index():
    try:
        resp = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(resp[-1][1])
    except:
        return 2.0


def get_diurnal_trend(total_hours, lat, date):
    day_of_year = date.timetuple().tm_yday
    seasonal = 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    diurnal = 10.0 + 15.0 * math.cos(math.pi * (total_hours - 14) / 12)
    return round(diurnal * (math.cos(math.radians(lat))) * seasonal, 2)


st.title("🛰 IonoSeis AI: Экспертный мониторинг")

if st.button("🔊 Активировать звуковые оповещения"):
    st.session_state.audio_activated = True

sensitivity = st.sidebar.slider("Порог чувствительности (Z-score)", 0.5, 2.0, 1.0, 0.1)
kp = get_real_kp_index()
st.info(f"🌐 Kp-индекс: **{kp}**")

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")

    # Берем точное время с точностью до секунд
    now = datetime.now(timezone.utc) + timedelta(hours=offset)
    total_hours = now.hour + now.minute / 60 + now.second / 3600

    # Теперь значение меняется каждую секунду
    base_norm = get_diurnal_trend(total_hours, lat, now)
    val = base_norm + (kp * 0.5)

    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    z = (val - base_norm) / (1.5 + (kp * 0.2))

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.subheader(f"📍 {city}")
        st.write(f"🕒 Время: **{now.strftime('%H:%M:%S')}**")
        st.metric("VTEC", f"{val:.2f}", f"{z:.2f}σ")
    with col2:
        if abs(z) > sensitivity:
            st.warning("⚠️ АНОМАЛИЯ")
        else:
            st.success("✅ Стабильно")
    with col3:
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='red' if abs(z) > sensitivity else 'cyan')
        ax.axis('off')
        st.pyplot(fig)

time.sleep(1)  # Обновление каждую секунду
st.rerun()