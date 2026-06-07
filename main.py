import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import math
import time
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Professional Monitoring")

CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}

if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}


# --- НАУЧНЫЕ ФУНКЦИИ ---
def get_space_weather_data():
    try:
        resp_f107 = requests.get("https://services.swpc.noaa.gov/products/noaa-f10.7-flux-between-events.json",
                                 timeout=5).json()
        f107 = float(resp_f107[-1][1])
        resp_kp = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        kp = float(resp_kp[-1][1])
        return kp, f107
    except:
        return 2.0, 150.0


def haversine_distance(lat1, lon1, lat2, lon2):
    # Расчет расстояния в км между двумя точками
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")
kp, f107 = get_space_weather_data()
st.info(f"🌐 Kp: **{kp}** | ☀️ Поток F10.7: **{f107}**")

try:
    quakes = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=" +
                          (datetime.now() - timedelta(days=1)).isoformat(), timeout=5).json()
except:
    quakes = {'features': []}

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")
    local_now = datetime.now(timezone.utc) + timedelta(hours=offset)

    # Расчет VTEC
    hour = local_now.hour + local_now.minute / 60.0
    day_of_year = local_now.timetuple().tm_yday
    seasonal = 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    base_norm = (8.0 + (f107 / 20.0) + 15.0 * math.cos(math.pi * (hour - 14) / 12)) * math.cos(
        math.radians(lat)) * seasonal

    val = base_norm + np.random.normal(0, 0.5 + (kp * 0.1))
    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    z = (val - base_norm) / (1.5 + (kp * 0.2))

    # Поиск землетрясений
    found = []
    for f in quakes.get('features', []):
        dist = haversine_distance(lat, lon, f['geometry']['coordinates'][1], f['geometry']['coordinates'][0])
        if dist < 1000:
            found.append((f, dist))

    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        st.subheader(f"📍 {city}")
        st.metric("VTEC", f"{val:.1f}", f"{z:.1f}σ")
    with col2:
        st.write("Ионосфера:")
        st.warning("⚠️ АНОМАЛИЯ") if abs(z) > 1.5 else st.info("✅ Стабильно")
    with col3:
        st.write("Сейсмика:")
        if found:
            q, dist = found[0]
            q_time = datetime.fromtimestamp(q['properties']['time'] / 1000, tz=timezone.utc).strftime('%H:%M')
            st.error(f"⚠️ M{q['properties']['mag']}")
            st.caption(f"📍 {q['properties']['place']}")
            st.caption(f"🕒 {q_time} UTC | 📏 {int(dist)} км")
        else:
            st.success("✅ Спокойно")
    with col4:
        fig, ax = plt.subplots(figsize=(6, 1.2))
        ax.plot(st.session_state.history[city], color='red' if abs(z) > 1.5 else 'cyan', linewidth=2.5)
        ax.axis('off')
        st.pyplot(fig)

time.sleep(5)
st.rerun()