import streamlit as st
import json
import pandas as pd
import requests
import pydeck as pdk
import time
import os
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI", page_icon="🛰️")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'vtec_data.json')

CITIES = {
    "Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65), "Тайвань (Хуалянь)": (24.00, 121.60), "Стамбул": (41.00, 28.97)
}


# --- ФУНКЦИИ ---

@st.cache_data(ttl=60)
def load_vtec_data():
    """Чтение данных из локального файла JSON"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


@st.cache_data(ttl=300)
def get_seismic_data():
    """Получение землетрясений 4.5+ за последние 3 дня"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=3)
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time.strftime('%Y-%m-%d')}&minmagnitude=4.5"
    try:
        res = requests.get(url, timeout=5).json()
        features = res.get('features', [])
        data = []
        for f in features:
            props = f['properties']
            data.append({
                "Магнитуда": props['mag'],
                "Место": props['place'],
                "Время": datetime.fromtimestamp(props['time'] / 1000).strftime('%d.%m %H:%M')
            })
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()


def get_kp():
    try:
        res = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(res[-1][1])
    except:
        return 2.0


# --- ИНТЕРФЕЙС ---
data = load_vtec_data()

st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
st.metric("Индекс солнечной активности (Kp)", f"{get_kp()} (Kp)")

tabs = st.tabs(["🟢 МОНИТОРИНГ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tabs[0]:
    st.write(f"🕒 **Последний скан данных:** {data.get('timestamp', 'Нет данных')}")
    cols = st.columns(5)
    for i, (city, (lat, lon)) in enumerate(CITIES.items()):
        val = data.get(city, 15.0)
        z = (val - 15.0) / 1.5
        with cols[i]:
            st.metric(city, f"{val:.1f} TECU", f"Z: {z:+.1f}")
            color = [255, 0, 0, 160] if abs(z) > 2.0 else [60, 200, 60, 160]
            st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=4),
                                     layers=[pdk.Layer("ScatterplotLayer", pd.DataFrame({'lat': [lat], 'lon': [lon]}),
                                                       get_position=["lon", "lat"], get_fill_color=color,
                                                       get_radius=60000)]))

with tabs[1]:
    st.subheader("Сейсмическая активность (4.5+ магнитуд за 3 дня)")
    df_quakes = get_seismic_data()
    if not df_quakes.empty:
        def highlight_mag(row):
            return ['background-color: #ffcccc' if row['Магнитуда'] >= 5.0 else '' for _ in row]


        st.dataframe(df_quakes.style.apply(highlight_mag, axis=1), use_container_width=True)
    else:
        st.write("Нет значимых событий.")

with tabs[2]:
    st.markdown("""
    ### 🧪 Методология: VTEC и литосферно-ионосферные связи (LIS)
    Система базируется на концепции пресейсмической ионизации ионосферы.

    1. **Физический процесс:** Перед землетрясениями в зоне разлома происходит накопление напряжений, что приводит к росту электронной плотности (VTEC) в ионосфере.
    2. **Z-score:** Статистический параметр *Z = (VTEC_current - VTEC_mean) / σ*. 
       - Значение **Z > 2.0** является сигналом аномалии.
    """)
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Ionosphere_layers.png", caption="Структура ионосферы")