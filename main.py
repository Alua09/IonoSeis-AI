import streamlit as st
import json
import pandas as pd
import requests
import pydeck as pdk
import time
from datetime import datetime, timezone, timedelta
import pytz

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI", page_icon="🛰️")

# Настройки времени
CITY_TZ = {
    "Алматы": "Asia/Almaty", "Бишкек": "Asia/Bishkek",
    "Токио": "Asia/Tokyo", "Тайвань (Хуалянь)": "Asia/Taipei", "Стамбул": "Europe/Istanbul"
}

CITIES_COORDS = {
    "Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65), "Тайвань (Хуалянь)": (24.00, 121.60), "Стамбул": (41.00, 28.97)
}


@st.cache_data(ttl=10800)  # Обновление кэша каждые 3 часа
def load_vtec_data():
    try:
        with open('vtec_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {city: 15.0 for city in CITIES_COORDS}


def get_kp():
    try:
        res = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(res[-1][1])
    except:
        return 2.0


# --- БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("🛰️ IonoSeis AI")
    st.write(f"🕒 **Время в Алматы:** {datetime.now(pytz.timezone('Asia/Almaty')).strftime('%H:%M:%S')}")
    st.divider()
    st.write("🌍 **Источники:** NASA, USGS, NOAA")

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
st.metric("Индекс солнечной активности (Kp)", f"{get_kp()} (Kp)")

data = load_vtec_data()
tabs = st.tabs(["🟢 МОНИТОРИНГ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tabs[0]:
    cols = st.columns(5)
    for i, (city, (lat, lon)) in enumerate(CITIES_COORDS.items()):
        val = data.get(city, 15.0)
        z = (val - 15.0) / 1.5
        local_time = datetime.now(pytz.timezone(CITY_TZ[city])).strftime('%H:%M')
        with cols[i]:
            st.metric(city, f"{val:.1f} TECU", f"Z: {z:+.1f}")
            st.caption(f"🕒 {local_time} (местное)")
            st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=4),
                                     layers=[pdk.Layer("ScatterplotLayer", pd.DataFrame({'lat': [lat], 'lon': [lon]}),
                                                       get_position=["lon", "lat"], get_fill_color=[255, 0, 0, 160],
                                                       get_radius=60000)]))

with tabs[1]:
    st.subheader("🌋 Сейсмическая активность (последние 72 часа)")
    three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    for city, (lat, lon) in CITIES_COORDS.items():
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=5.0&starttime={three_days_ago}"
        try:
            quakes = requests.get(url, timeout=5).json().get('features', [])
            for q in quakes:
                ts = datetime.fromtimestamp(q['properties']['time'] / 1000).strftime('%d.%m %H:%M')
                st.error(f"⚠️ {city}: {ts} | {q['properties']['mag']} M | {q['properties']['place']}")
        except:
            pass

with tabs[2]:
    st.markdown("### Принцип LIS: Ионизация как прекурсор")
    st.markdown("Система анализирует аномалии VTEC, возникающие из-за эмиссии радона перед сейсмическим событием.")

time.sleep(60)
st.rerun()