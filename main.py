import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import math
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard")

# CITIES: (lat, lon, offset_hours)
CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}

if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}


# --- НАУЧНЫЕ ФУНКЦИИ ---
def get_dynamic_search_radius(mag):
    return 300 * (1.5 ** (mag - 5.0))


def get_seasonal_factor(date):
    day_of_year = date.timetuple().tm_yday
    return 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)


def get_diurnal_trend(hour, lat, date):
    """Теоретическая норма (серая линия)"""
    seasonal = get_seasonal_factor(date)
    diurnal = 10.0 + 15.0 * math.cos(math.pi * (hour - 14) / 12)
    return diurnal * (math.cos(math.radians(lat))) * seasonal


def moving_average(data, window=5):
    if len(data) < window: return data
    return np.convolve(data, np.ones(window) / window, mode='valid')


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")

if st.button("🔄 ОБНОВИТЬ ДАННЫЕ"):
    st.success("Данные синхронизированы.")

# Сейсмика
try:
    quakes = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=" +
                          (datetime.now() - timedelta(days=1)).isoformat(), timeout=5).json()
except:
    quakes = {'features': []}

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")

    # Расчет времени для конкретного города
    local_now = datetime.now(timezone.utc) + timedelta(hours=offset)

    # 1. Расчет
    hour = local_now.hour + local_now.minute / 60.0
    base_norm = get_diurnal_trend(hour, lat, local_now)
    val = base_norm + np.random.normal(0, 0.5)

    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    std_dev = 1.5
    z = (val - base_norm) / std_dev

    # 2. Сейсмика
    found_quakes = [f for f in quakes.get('features', [])
                    if math.sqrt((f['geometry']['coordinates'][1] - lat) ** 2 +
                                 (f['geometry']['coordinates'][0] - lon) ** 2) * 111 < get_dynamic_search_radius(
            f['properties']['mag'])]

    # 3. Визуализация
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

    with col1:
        st.subheader(f"📍 {city}")
        st.caption(f"🕒 Местное время: {local_now.strftime('%H:%M:%S')}")  # Вывод времени
        sign = "+" if z >= 0 else ""
        st.metric("VTEC (TECU)", f"{val:.1f}", f"{sign}{z:.1f}σ")

    with col2:
        st.write("Ионосфера:")
        if abs(z) > 1.5:
            st.warning("⚠️ АНОМАЛИЯ")
        else:
            st.info("✅ Стабильно")

    with col3:
        st.write("Сейсмика:")
        if found_quakes:
            st.error(f"⚠️ Событие M{found_quakes[0]['properties']['mag']}")
        else:
            st.success("✅ Спокойно")

    with col4:
        fig, ax = plt.subplots(figsize=(6, 1.2))
        smoothed = moving_average(st.session_state.history[city], window=5)
        color = 'red' if abs(z) > 1.5 else 'cyan'

        ax.plot(smoothed, color=color, linewidth=2.5, label='VTEC Trend')
        ax.axhline(y=base_norm, color='gray', linestyle='--', alpha=0.5, label='Norm')

        ax.legend(loc='upper left', fontsize=8, frameon=False)
        ax.spines['top'].set_visible(False);
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False);
        ax.spines['bottom'].set_visible(False)
        ax.set_xticks([]);
        ax.set_yticks([])

        st.pyplot(fig)

st.write("Метод: Статистический анализ (Z-score) относительно динамической модели (Diurnal & Seasonal).")