import streamlit as st
import numpy as np
import requests
import pandas as pd
import pydeck as pdk
from datetime import datetime, timezone

st.set_page_config(layout="wide", page_title="IonoSeis AI", page_icon="🛰️")

# --- СТИЛЬ ---
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #f0fdf4; border: 1px solid #22c55e; padding: 5px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

CITIES = {"Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59), "Токио": (35.68, 139.65),
          "Тайвань (Хуалянь)": (24.00, 121.60), "Стамбул": (41.00, 28.97)}

if 'history' not in st.session_state:
    st.session_state.history = {city: [15.0] * 20 for city in CITIES}


# --- ФУНКЦИИ ---
def get_space_weather_data():
    return 2.1, 145.0


def get_recent_quakes(lat, lon):
    try:
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=3.0&limit=3"
        return requests.get(url, timeout=3).json().get('features', [])
    except:
        return []


# --- ИНТЕРФЕЙС ---
st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
kp, f107 = get_space_weather_data()

c1, c2, c3 = st.columns(3)
c1.metric("**Kp-индекс**", kp)
c2.metric("**Поток F10.7**", f107)
c3.metric("**Время UTC**", datetime.now(timezone.utc).strftime('%H:%M:%S'))

tab1, tab2, tab3, tab4 = st.tabs(["🟢 МОНИТОРИНГ", "🚨 АНОМАЛИИ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1:
    for city, (lat, lon) in CITIES.items():
        # Динамика данных
        val = 15.0 + np.random.normal(0, 0.3)
        st.session_state.history[city].append(val)
        st.session_state.history[city].pop(0)

        with st.container(border=True):
            st.subheader(f"📍 {city}")
            m1, m2, m3, g1, m4 = st.columns([1, 1, 1, 2, 1])
            m1.metric("**VTEC**", f"{val:.1f} TECU")
            m2.metric("**СТАТУС**", "НОРМА" if val < 16 else "АНОМАЛИЯ")
            m3.metric("**СЕЙСМИКА**", "OK")
            g1.line_chart(st.session_state.history[city], color="#2dd4bf", height=80)

            # Квадратная компактная карта
            df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
            m4.pydeck_chart(pdk.Deck(
                initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=4),
                layers=[pdk.Layer("ScatterplotLayer", df, get_position=["lon", "lat"], get_fill_color=[255, 0, 0],
                                  get_radius=50000)]
            ))

with tab3:
    for city, (lat, lon) in CITIES.items():
        st.write(f"### {city}")
        for q in get_recent_quakes(lat, lon):
            mag = q['properties']['mag']
            text = f"Magnitude {mag} - {q['properties']['place']}"
            if mag >= 5.0:
                st.error(f"⚠️ {text}")
            else:
                st.write(text)

with tab4:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Ionosphere_layers.svg/600px-Ionosphere_layers.svg.png")
    st.markdown("### Как работает IonoSeis AI (Концепция LIS)...")
    st.latex(r"Z = \frac{VTEC_{obs} - VTEC_{norm}}{\sigma}")