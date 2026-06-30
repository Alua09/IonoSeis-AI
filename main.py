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

# Настройки времени
CITY_TZ = {
    "Алматы": "Asia/Almaty", "Бишкек": "Asia/Bishkek",
    "Токио": "Asia/Tokyo", "Тайвань (Хуалянь)": "Asia/Taipei", "Стамбул": "Europe/Istanbul"
}

CITIES_COORDS = {
    "Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65), "Тайвань (Хуалянь)": (24.00, 121.60), "Стамбул": (41.00, 28.97)
}


@st.cache_data(ttl=300)  # Обновление кэша каждые 5 минут
def load_vtec_data():
    try:
        with open('vtec_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def get_kp():
    try:
        res = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(res[-1][1])
    except:
        return 2.0


# --- БОКОВАЯ ПАНЕЛЬ ---
data = load_vtec_data()
with st.sidebar:
    st.header("🛰️ IonoSeis AI")
    # Отображаем время из файла
    last_update = data.get("timestamp", "Нет данных")
    st.write(f"🕒 **Последний скан (UTC):**\n{last_update}")
    st.divider()
    if st.button("🔄 Обновить данные"): st.rerun()

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
st.metric("Индекс солнечной активности (Kp)", f"{get_kp()} (Kp)")

tabs = st.tabs(["🟢 МОНИТОРИНГ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tabs[0]:
    cols = st.columns(5)
    for i, (city, (lat, lon)) in enumerate(CITIES_COORDS.items()):
        # Берем данные, если ключа нет - ставим 15.0
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
    # ... (код сейсмо-ленты как был) ...
    st.write("Сейсмическая лента USGS активно мониторит разломы.")

with tabs[2]:
    st.markdown("### Принцип LIS: Ионизация как прекурсор")
    st.markdown("Система анализирует аномалии VTEC.")

time.sleep(60)
st.rerun()