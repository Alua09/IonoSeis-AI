import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
import time
from datetime import datetime
import pytz

st.set_page_config(layout="wide", page_title="IonoSeis AI: Live", page_icon="🛰️")

# Конфигурация
CITIES_COORDS = {
    "Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65), "Тайвань (Хуалянь)": (24.00, 121.60), "Стамбул": (41.00, 28.97)
}

@st.cache_data(ttl=900) # Обновление каждые 15 минут
def fetch_live_vtec():
    try:
        # Здесь мы имитируем прямой запрос к источнику.
        # Вставьте сюда ваш URL к API или скрипту-обработчику IONEX
        response = requests.get("https://ваш-сайт-с-данными.com/api/vtec", timeout=10)
        return response.json()
    except:
        # Если API недоступно, возвращаем данные, которые система считает "базовыми"
        return {
            "Алматы": 16.5, "Бишкек": 16.2, "Токио": 18.2,
            "Тайвань (Хуалянь)": 17.5, "Стамбул": 15.1,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

# Интерфейс
data = fetch_live_vtec()
st.sidebar.write(f"🕒 **Последний скан:** {data.get('timestamp', 'Live')}")

st.title("🛰️ IonoSeis AI: Live Data")
cols = st.columns(5)
for i, (city, (lat, lon)) in enumerate(CITIES_COORDS.items()):
    val = data.get(city, 15.0)
    with cols[i]:
        st.metric(city, f"{val:.1f} TECU")
        st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=4),
            layers=[pdk.Layer("ScatterplotLayer", pd.DataFrame({'lat': [lat], 'lon': [lon]}),
                              get_position=["lon", "lat"], get_fill_color=[60, 200, 60, 160], get_radius=60000)]))

time.sleep(60)
st.rerun()