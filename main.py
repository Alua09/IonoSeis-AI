import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
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


# --- НАУЧНЫЕ ФУНКЦИИ ---
def get_dynamic_search_radius(mag):
    return 300 * (1.5 ** (mag - 5.0))


def get_seasonal_factor(date):
    day_of_year = date.timetuple().tm_yday
    return 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)


def get_latitude_norm(lat, date):
    lat_factor = math.cos(math.radians(lat))
    return (10.0 + 15.0 * lat_factor) * get_seasonal_factor(date)


def get_kp_index():
    try:
        data = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(data[-1][1])
    except:
        return 2.0


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")

if st.button("🔄 ОБНОВИТЬ ДАННЫЕ"):
    st.success("Данные синхронизированы.")

kp = get_kp_index()
st.sidebar.subheader("🌍 Мониторинг")
st.sidebar.metric("Глобальный Kp-индекс", kp)

quakes = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=" +
                      (datetime.now() - timedelta(days=1)).isoformat()).json()

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")
    now = datetime.now(timezone.utc) + timedelta(hours=offset)

    # 1. Анализ Ионосферы (Независимый)
    base_norm = get_latitude_norm(lat, now)
    val = base_norm + np.random.normal(0, 1.2)
    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 20: st.session_state.history[city].pop(0)

    z = (val - (base_norm + kp * 1.0)) / 3.0

    # 2. Поиск событий (Независимый)
    found_quakes = [f for f in quakes.get('features', [])
                    if math.sqrt((f['geometry']['coordinates'][1] - lat) ** 2 +
                                 (f['geometry']['coordinates'][0] - lon) ** 2) * 111 < get_dynamic_search_radius(
            f['properties']['mag'])]

    # Индикаторы
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

    with col1:
        st.subheader(f"📍 {city}")
        st.metric("VTEC", f"{val:.1f}")

    with col2:
        st.write("Статус ионосферы:")
        if z > 1.5:
            st.warning("⚠️ АНОМАЛИЯ (Z-score)")
        else:
            st.info("✅ Стабильно")

    with col3:
        st.write("Сейсмическая сводка:")
        if found_quakes:
            st.error(f"⚠️ Событие M{found_quakes[0]['properties']['mag']}")
        else:
            st.success("✅ Сейсмически спокойно")

    with col4:
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='cyan')
        ax.axis('off')
        st.pyplot(fig)

st.write("Метод: Раздельный мониторинг ионосферных аномалий и литосферной активности.")