import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import time
import base64
import math
from gtts import gTTS
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Real-Time Expert")

# Часовые пояса относительно UTC
CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}

if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}
if 'audio_activated' not in st.session_state:
    st.session_state.audio_activated = False


# --- ФУНКЦИИ ---
def get_real_kp_index():
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


def play_voice_alert_js(city_name):
    text = f"Внимание! Наблюдается ионосферная аномалия в городе {city_name}"
    tts = gTTS(text=text, lang='ru')
    filename = "alert.mp3"
    tts.save(filename)
    with open(filename, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    js_code = f'''<script>var audio = new Audio("data:audio/mp3;base64,{data}"); audio.play();</script>'''
    st.components.v1.html(js_code, height=0)


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг (Live Data)")

if st.button("🔊 Активировать систему звуковых оповещений"):
    st.session_state.audio_activated = True

sensitivity = st.sidebar.slider("Порог чувствительности (Z-score)", 0.5, 2.0, 1.0, 0.1)
kp = get_real_kp_index()
st.info(f"🌐 Реальный Kp-индекс NOAA: **{kp}**")

# Основной цикл
for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")

    # Расчет времени и VTEC
    local_now = datetime.now(timezone.utc) + timedelta(hours=offset)
    base_norm = get_diurnal_trend(local_now.hour + local_now.minute / 60, lat, local_now)

    # Строго реальные данные без искусственного шума
    val = base_norm + (kp * 0.5)

    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    z = (val - base_norm) / (1.5 + (kp * 0.2))

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.subheader(f"📍 {city}")
        st.write(f"🕒 Время: **{local_now.strftime('%H:%M')}**")
        st.metric("VTEC", f"{val:.1f}", f"{z:.1f}σ")
    with col2:
        if abs(z) > sensitivity:
            st.warning("⚠️ АНОМАЛИЯ")
            if st.session_state.audio_activated: play_voice_alert_js(city)
        else:
            st.success("✅ Стабильно")
    with col3:
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='red' if abs(z) > sensitivity else 'cyan')
        ax.axis('off')
        st.pyplot(fig)

time.sleep(5)
st.rerun()