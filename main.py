import streamlit as st
import json
import pandas as pd
import requests
import pydeck as pdk
from datetime import datetime, timezone, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI", page_icon="🛰️")


# Чтение "живых" данных из файла
def load_data():
    try:
        with open('vtec_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"Алматы": 15.0, "Бишкек": 15.0, "Токио": 15.0, "Тайвань (Хуалянь)": 15.0, "Стамбул": 15.0}


@st.cache_data(ttl=300)
def get_kp():
    try:
        res = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(res[-1][1])
    except:
        return 2.0


CITIES = {
    "Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65), "Тайвань (Хуалянь)": (24.00, 121.60), "Стамбул": (41.00, 28.97)
}

st.title("🛰️ IonoSeis AI: Реальный мониторинг")
kp = get_kp()
st.metric("Текущий Kp-индекс", f"{kp} (Kp)")

data = load_data()
tabs = st.tabs(["🟢 МОНИТОРИНГ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tabs[0]:
    cols = st.columns(5)
    for i, (city, (lat, lon)) in enumerate(CITIES.items()):
        val = data.get(city, 15.0)
        z = (val - 15.0) / 1.5
        with cols[i]:
            st.metric(city, f"{val:.1f} TECU", f"{z:+.1f}σ")
            color = [255, 0, 0, 160] if abs(z) > 2.0 else [60, 200, 60, 160]
            st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=4),
                                     layers=[pdk.Layer("ScatterplotLayer", pd.DataFrame({'lat': [lat], 'lon': [lon]}),
                                                       get_position=["lon", "lat"], get_fill_color=color,
                                                       get_radius=60000)]))

with tabs[1]:
    for city, (lat, lon) in CITIES.items():
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=5.0"
        quakes = requests.get(url, timeout=5).json().get('features', [])
        for q in quakes:
            st.error(f"⚠️ {city}: {q['properties']['mag']} M | {q['properties']['place']}")

with tabs[2]:
    st.markdown("### Принцип LIS: Ионизация как прекурсор")
    st.markdown("Система анализирует аномалии VTEC, возникающие из-за эмиссии радона перед сейсмическим событием.")

import time

time.sleep(60)
st.rerun()