import streamlit as st
import json
import pandas as pd
import requests
import pydeck as pdk
import time
from datetime import datetime
import pytz

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard", page_icon="🛰️")

# Настройки времени для городов
CITY_TZ = {
    "Алматы": "Asia/Almaty", "Бишкек": "Asia/Bishkek",
    "Токио": "Asia/Tokyo", "Тайвань (Хуалянь)": "Asia/Taipei", "Стамбул": "Europe/Istanbul"
}

CITIES_COORDS = {
    "Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65), "Тайвань (Хуалянь)": (24.00, 121.60), "Стамбул": (41.00, 28.97)
}


# --- ФУНКЦИИ ---
@st.cache_data(ttl=900)  # Обновление данных каждые 15 минут (900 сек)
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
    almaty_tz = pytz.timezone("Asia/Almaty")
    st.write(f"🕒 **Время в Алматы:** {datetime.now(almaty_tz).strftime('%H:%M:%S')}")
    st.divider()
    st.write("🌍 **Источники:** NASA CDDIS, USGS, NOAA")
    if st.button("🔄 Обновить сейчас"): st.rerun()

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
st.metric("Текущий индекс солнечной активности (Kp)", f"{get_kp()} (Kp)")

data = load_vtec_data()
tab1, tab2, tab3 = st.tabs(["🟢 МОНИТОРИНГ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1:
    cols = st.columns(5)
    for i, (city, (lat, lon)) in enumerate(CITIES_COORDS.items()):
        val = data.get(city, 15.0)
        z = (val - 15.0) / 1.5

        # Локальное время города
        tz = pytz.timezone(CITY_TZ.get(city, "UTC"))
        local_time = datetime.now(tz).strftime('%H:%M')

        with cols[i]:
            st.metric(city, f"{val:.1f} TECU", f"Z: {z:+.1f}")
            st.caption(f"🕒 {local_time} (местное)")
            color = [255, 0, 0, 160] if abs(z) > 2.0 else [60, 200, 60, 160]
            st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=4),
                                     layers=[pdk.Layer("ScatterplotLayer", pd.DataFrame({'lat': [lat], 'lon': [lon]}),
                                                       get_position=["lon", "lat"], get_fill_color=color,
                                                       get_radius=60000)]))

with tab2:
    st.subheader("🌋 Сейсмическая активность (последние 72 часа)")
    from datetime import timezone, timedelta

    three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    for city, (lat, lon) in CITIES_COORDS.items():
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=5.0&starttime={three_days_ago}"
        try:
            quakes = requests.get(url, timeout=5).json().get('features', [])
            for q in quakes:
                ts = datetime.fromtimestamp(q['properties']['time'] / 1000).strftime('%d.%m %H:%M')
                st.error(f"⚠️ {city}: {ts} | {q['properties']['mag']} M | {q['properties']['place']}")
        except:
            continue

with tab3:
    st.subheader("🧪 Научная концепция LIS")
    st.markdown("Анализ ионосферных аномалий (VTEC) как индикаторов сейсмического напряжения.")

# Автообновление раз в минуту
time.sleep(60)
st.rerun()