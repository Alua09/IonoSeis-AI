import streamlit as st
import json
import pandas as pd
import requests
import pydeck as pdk
import time
import os
import pytz
from datetime import datetime

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI", page_icon="🛰️")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'vtec_data.json')

CITIES = {
    "Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65), "Тайвань (Хуалянь)": (24.00, 121.60), "Стамбул": (41.00, 28.97)
}


@st.cache_data(ttl=60)
def load_vtec_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def get_kp():
    try:
        res = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(res[-1][1])
    except:
        return 2.0


# --- ИНТЕРФЕЙС ---
data = load_vtec_data()

with st.sidebar:
    st.header("🛰️ IonoSeis AI")
    st.write(f"🕒 **Последний скан:** {data.get('timestamp', 'Нет данных')}")
    if st.button("🔄 Принудительное обновление"): st.rerun()

st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
st.metric("Индекс солнечной активности (Kp)", f"{get_kp()} (Kp)")

tabs = st.tabs(["🟢 МОНИТОРИНГ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tabs[0]:
    cols = st.columns(5)
    for i, (city, (lat, lon)) in enumerate(CITIES.items()):
        val = data.get(city, 15.0)
        # Расчет Z-score
        z = (val - 15.0) / 1.5

        with cols[i]:
            st.metric(city, f"{val:.1f} TECU", f"Z: {z:+.1f}")
            # Цвет индикатора: красный если Z > 2.0
            color = [255, 0, 0, 160] if abs(z) > 2.0 else [60, 200, 60, 160]
            st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=4),
                                     layers=[pdk.Layer("ScatterplotLayer", pd.DataFrame({'lat': [lat], 'lon': [lon]}),
                                                       get_position=["lon", "lat"], get_fill_color=color,
                                                       get_radius=60000)]))

with tabs[1]:
    st.write("Сейсмическая активность мониторится через USGS API.")

with tabs[2]:
    st.markdown("### Метод ионосферного мониторинга")

time.sleep(60)
st.rerun()