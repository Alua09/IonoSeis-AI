import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import math
import time
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Scientific Expert")

CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}

if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}


# --- НАУЧНЫЕ ФУНКЦИИ ---
def get_space_weather_data():
    """Получает Kp и F10.7 из единого источника NOAA."""
    try:
        # NOAA F10.7 flux data
        resp_f107 = requests.get("https://services.swpc.noaa.gov/products/noaa-f10.7-flux-between-events.json",
                                 timeout=5).json()
        f107 = float(resp_f107[-1][1])

        # NOAA Kp index
        resp_kp = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        kp = float(resp_kp[-1][1])

        return kp, f107
    except:
        return 2.0, 150.0  # Средние значения по умолчанию


def get_diurnal_trend(hour, lat, date, f107):
    day_of_year = date.timetuple().tm_yday
    seasonal = 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    # Ионизация теперь прямо зависит от F10.7
    ionization_base = 8.0 + (f107 / 20.0)
    diurnal = ionization_base + 15.0 * math.cos(math.pi * (hour - 14) / 12)
    return round(diurnal * (math.cos(math.radians(lat))) * seasonal, 1)


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Анализ солнечного влияния")

kp, f107 = get_space_weather_data()
col_a, col_b = st.columns(2)
col_a.metric("🌐 Kp-индекс", kp)
col_b.metric("☀️ Поток F10.7", f107)

# Сейсмика
try:
    quakes = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=" +
                          (datetime.now() - timedelta(days=1)).isoformat(), timeout=5).json()
except:
    quakes = {'features': []}

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")
    local_now = datetime.now(timezone.utc) + timedelta(hours=offset)
    hour = local_now.hour + local_now.minute / 60.0

    # 1. Расчет с учетом F10.7
    base_norm = get_diurnal_trend(hour, lat, local_now, f107)
    val = base_norm + np.random.normal(0, 0.5 + (kp * 0.1))

    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    z = (val - base_norm) / (1.5 + (kp * 0.2))

    # 2. Визуализация и Сейсмика
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.subheader(f"📍 {city}")
        st.metric("VTEC", f"{val:.1f}", f"{z:.1f}σ")
    with col2:
        if abs(z) > 1.5:
            st.warning("⚠️ АНОМАЛИЯ")
        else:
            st.success("✅ Стабильно")
    with col3:
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='red' if abs(z) > 1.5 else 'cyan')
        st.axis('off')
        st.pyplot(fig)

time.sleep(5)
st.rerun()