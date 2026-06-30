import streamlit as st
import json
import pandas as pd
import requests
import pydeck as pdk
import os
import pytz
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI", page_icon="🛰️")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'vtec_data.json')

CITIES = {
    "Алматы": (43.25, 76.92, "Asia/Almaty"),
    "Бишкек": (42.87, 74.59, "Asia/Bishkek"),
    "Токио": (35.68, 139.65, "Asia/Tokyo"),
    "Тайвань (Хуалянь)": (24.00, 121.60, "Asia/Taipei"),
    "Стамбул": (41.00, 28.97, "Europe/Istanbul")
}


# --- ФУНКЦИИ ---
def haversine(lat1, lon1, lat2, lon2):
    """Расстояние в км между двумя точками"""
    R = 6371
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon / 2) ** 2
    return R * 2 * asin(sqrt(a))


@st.cache_data(ttl=300)
def get_filtered_seismic_data():
    """Землетрясения 4.0+ в радиусе 500км от наших городов"""
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=4.0&limit=200"
    try:
        res = requests.get(url, timeout=10).json()
        data = []
        for f in res['features']:
            props = f['properties']
            coords = f['geometry']['coordinates']  # [lon, lat]
            quake_lat, quake_lon = coords[1], coords[0]

            # Проверка дистанции до любого из городов
            for city, (c_lat, c_lon, _) in CITIES.items():
                if haversine(quake_lat, quake_lon, c_lat, c_lon) < 500:
                    data.append({
                        "Магнитуда": props['mag'],
                        "Ближайший город": city,
                        "Место": props['place'],
                        "Время": datetime.fromtimestamp(props['time'] / 1000).strftime('%d.%m %H:%M')
                    })
                    break
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()


def load_vtec_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


# --- ИНТЕРФЕЙС ---
data = load_vtec_data()

# БОКОВАЯ ПАНЕЛЬ
with st.sidebar:
    st.header("🛰️ IonoSeis AI")
    st.write(f"🕒 **Последний скан (UTC):** {data.get('timestamp', 'Нет данных')}")
    st.info("Мониторинг литосферно-ионосферных связей.")

st.title("🛰️ IonoSeis AI: Экспертный мониторинг")

tabs = st.tabs(["🟢 МОНИТОРИНГ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tabs[0]:
    cols = st.columns(5)
    for i, (city, (lat, lon, tz)) in enumerate(CITIES.items()):
        val = data.get(city, 15.0)
        z = (val - 15.0) / 1.5
        local_time = datetime.now(pytz.timezone(tz)).strftime('%H:%M')
        with cols[i]:
            st.metric(city, f"{val:.1f} TECU", f"Z: {z:+.1f}")
            st.caption(f"🕒 {local_time} (местное)")
            color = [255, 0, 0, 160] if abs(z) > 2.0 else [60, 200, 60, 160]
            st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=4),
                                     layers=[pdk.Layer("ScatterplotLayer", pd.DataFrame({'lat': [lat], 'lon': [lon]}),
                                                       get_position=["lon", "lat"], get_fill_color=color,
                                                       get_radius=60000)]))

with tabs[1]:
    st.subheader("Сейсмическая активность в целевых регионах (4.0+)")
    df = get_filtered_seismic_data()
    if not df.empty:
        st.dataframe(
            df.style.map(lambda x: 'background-color: #ffcccc' if isinstance(x, (int, float)) and x >= 5.0 else '',
                         subset=['Магнитуда']), use_container_width=True)
    else:
        st.write("В радиусе 500км от целевых городов значимых событий не зафиксировано.")

with tabs[2]:
    st.markdown("### 🧪 Научная методология")
    st.write("Ионосферные аномалии рассматриваются как индикаторы перераспределения напряжений в земной коре.")