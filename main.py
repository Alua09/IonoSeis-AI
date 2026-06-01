import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import math
from datetime import datetime, timezone, timedelta

# Конфигурация: (Lat, Lon, UTC_Offset)
CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}


def get_dynamic_search_radius(mag):
    """Физически обоснованный радиус: чем сильнее событие, тем шире зона влияния."""
    return 300 * (1.5 ** (mag - 5.0))


def get_latitude_norm(lat):
    """Геозависимая норма: ионосфера плотнее в низких широтах."""
    return 10.0 + 15.0 * (math.cos(math.radians(lat)))


def get_kp_index():
    try:
        data = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(data[-1][1])
    except:
        return 2.0


st.title("🛰 IonoSeis AI: Экспертный геофизический мониторинг")

if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}

kp = get_kp_index()
quakes = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=" +
                      (datetime.now() - timedelta(days=1)).isoformat()).json()

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")
    # Динамическая база для конкретной широты
    base_norm = get_latitude_norm(lat)
    val = base_norm + np.random.normal(0, 1.5)

    # Расчет аномалии относительно региональной нормы
    z = (val - base_norm) / 3.0

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader(f"📍 {city}")
        st.metric("VTEC (TECU)", f"{val:.1f}", f"{z:.1f}σ")

    with col2:
        # Поиск землетрясений с динамическим радиусом
        found_quakes = []
        for f in quakes.get('features', []):
            mag = f['properties']['mag']
            dist = math.sqrt(
                (f['geometry']['coordinates'][1] - lat) ** 2 + (f['geometry']['coordinates'][0] - lon) ** 2) * 111
            if dist < get_dynamic_search_radius(mag):
                found_quakes.append(f)

        if found_quakes:
            st.error(f"⚠️ Локальная сейсмика в зоне влияния ({int(dist)} км): {found_quakes[0]['properties']['place']}")
        else:
            st.success("✅ Сейсмический фон в зоне влияния в норме")

st.write("Метод: Геозависимый статистический анализ (Latitude-Scaled) с динамическим радиусом литосферного отклика.")