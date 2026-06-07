import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import math
import time
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
def get_space_weather_data():
    """Получение Kp и F10.7 из NOAA."""
    try:
        resp_f107 = requests.get("https://services.swpc.noaa.gov/products/noaa-f10.7-flux-between-events.json",
                                 timeout=5).json()
        f107 = float(resp_f107[-1][1])
        resp_kp = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        kp = float(resp_kp[-1][1])
        return kp, f107
    except:
        return 2.0, 150.0


def get_diurnal_trend(hour, lat, date, f107):
    day_of_year = date.timetuple().tm_yday
    seasonal = 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    ionization_base = 8.0 + (f107 / 20.0)
    diurnal = ionization_base + 15.0 * math.cos(math.pi * (hour - 14) / 12)
    return round(diurnal * (math.cos(math.radians(lat))) * seasonal, 1)


def moving_average(data, window=5):
    if len(data) < window: return data
    return np.convolve(data, np.ones(window) / window, mode='valid')


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")

kp, f107 = get_space_weather_data()
st.info(f"🌐 Геомагнитный индекс (Kp): **{kp}** | ☀️ Солнечный поток (F10.7): **{f107}**")

# Запрос к USGS (Сейсмика)
try:
    quakes = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=" +
                          (datetime.now() - timedelta(days=1)).isoformat(), timeout=5).json()
except:
    quakes = {'features': []}

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")
    local_now = datetime.now(timezone.utc) + timedelta(hours=offset)
    hour = local_now.hour + local_now.minute / 60.0

    # 1. Расчеты
    base_norm = get_diurnal_trend(hour, lat, local_now, f107)
    val = base_norm + np.random.normal(0, 0.5 + (kp * 0.1))

    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    std_dev = 1.5 + (kp * 0.2)
    z = (val - base_norm) / std_dev

    # 2. Поиск сейсмики в радиусе 1000 км
    found_quakes = [f for f in quakes.get('features', [])
                    if math.sqrt((f['geometry']['coordinates'][1] - lat) ** 2 +
                                 (f['geometry']['coordinates'][0] - lon) ** 2) * 111 < 1000]

    # 3. Визуализация
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

    with col1:
        st.subheader(f"📍 {city}")
        st.caption(f"🕒 Время: {local_now.strftime('%H:%M:%S')}")
        st.metric("VTEC (TECU)", f"{val:.1f}", f"{z:.1f}σ")

    with col2:
        st.write("Ионосфера:")
        if abs(z) > 1.5:
            st.warning("⚠️ АНОМАЛИЯ")
        else:
            st.info("✅ Стабильно")

    with col3:
        st.write("Сейсмика:")
        if found_quakes:
            st.error(f"⚠️ M{found_quakes[0]['properties']['mag']}")
        else:
            st.success("✅ Спокойно")

    with col4:
        fig, ax = plt.subplots(figsize=(6, 1.2))
        smoothed = moving_average(st.session_state.history[city], window=5)
        ax.plot(smoothed, color='red' if abs(z) > 1.5 else 'cyan', linewidth=2.5)
        ax.axhline(y=base_norm, color='gray', linestyle='--', alpha=0.5)
        ax.axis('off')  # ИСПРАВЛЕНО
        st.pyplot(fig)

time.sleep(5)
st.rerun()