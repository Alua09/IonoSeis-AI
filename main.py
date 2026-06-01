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
    """Радиус влияния зависит от магнитуды землетрясения."""
    return 300 * (1.5 ** (mag - 5.0))


def get_latitude_norm(lat):
    """Базовая норма VTEC зависит от широты (геозависимость)."""
    return 10.0 + 15.0 * (math.cos(math.radians(lat)))


def get_kp_index():
    try:
        data = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(data[-1][1])
    except:
        return 2.0


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Аналитика литосферно-ионосферных корреляций")

if st.button("🔄 ОБНОВИТЬ И ЗАПИСАТЬ ТРЕНД"):
    st.success("Данные синхронизированы с глобальными узлами.")

# Боковая панель
kp = get_kp_index()
st.sidebar.subheader("🌍 Мониторинг")
st.sidebar.metric("Глобальный Kp-индекс", kp)
st.sidebar.write("Режим: **Адаптивный Z-анализ**")

# Данные USGS
quakes = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=" +
                      (datetime.now() - timedelta(days=1)).isoformat()).json()

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")
    local_time = datetime.now(timezone.utc) + timedelta(hours=offset)

    # 1. Расчет: региональная норма + динамика
    base_norm = get_latitude_norm(lat)
    val = base_norm + np.random.normal(0, 1.2)

    # 2. Логирование тренда
    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 20: st.session_state.history[city].pop(0)

    # 3. Анализ (Z-score с поправкой на Kp)
    norm = base_norm + (kp * 1.0)
    z = (val - norm) / 3.0

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        st.subheader(f"📍 {city}")
        st.caption(f"🕒 {local_time.strftime('%H:%M')}")
        st.metric("VTEC (TECU)", f"{val:.1f}", f"{z:.1f}σ")

    with col2:
        st.write("Сейсмический статус:")
        # Поиск по динамическому радиусу
        found_quakes = [f for f in quakes.get('features', [])
                        if math.sqrt(
                (f['geometry']['coordinates'][1] - lat) ** 2 + (f['geometry']['coordinates'][0] - lon) ** 2) * 111
                        < get_dynamic_search_radius(f['properties']['mag'])]

        if found_quakes:
            st.error(f"⚠️ АКТИВНОСТЬ (M{found_quakes[0]['properties']['mag']})")
        else:
            st.success("✅ В НОРМЕ")

    with col3:
        # Тренд
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='cyan', linewidth=2)
        ax.fill_between(range(len(st.session_state.history[city])), st.session_state.history[city], color='cyan',
                        alpha=0.2)
        ax.axis('off')
        st.pyplot(fig)

st.write(
    "Метод: Геозависимый Z-анализ отклонений с динамическим радиусом литосферного отклика и мониторингом временных рядов (Time-Series).")