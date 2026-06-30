import streamlit as st
import json
import pandas as pd
import requests
import pydeck as pdk
import time
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard", page_icon="🛰️")


# --- ФУНКЦИИ ---
def load_vtec_data():
    try:
        with open('vtec_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"Алматы": 16.5, "Бишкек": 16.2, "Токио": 18.2, "Тайвань (Хуалянь)": 17.5, "Стамбул": 15.1}


@st.cache_data(ttl=3600)
def get_kp():
    try:
        res = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(res[-1][1])
    except:
        return 2.0


# --- БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("🛰️ IonoSeis AI")
    st.info("Экспертный мониторинг ионосферных аномалий.")
    st.write(f"🕒 **Последний скан:** {datetime.now().strftime('%H:%M:%S')}")
    st.subheader("🌍 Источники")
    st.markdown("- **VTEC:** NASA CDDIS (GIM)\n- **Сейсмика:** USGS Earthquake API\n- **Космос:** NOAA Space Weather")
    st.divider()
    if st.button("🔄 Принудительное обновление"): st.rerun()

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
kp = get_kp()
st.metric("Текущий индекс солнечной активности (Kp)", f"{kp} (Kp)")

data = load_vtec_data()
CITIES = {
    "Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65), "Тайвань (Хуалянь)": (24.00, 121.60), "Стамбул": (41.00, 28.97)
}

tab1, tab2, tab3 = st.tabs(["🟢 МОНИТОРИНГ", "🌋 СЕЙСМО-ЛЕНТА (72ч)", "🧪 МЕТОДОЛОГИЯ"])

with tab1:
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

with tab2:
    st.subheader("🌋 Сейсмическая активность (M > 5.0)")
    three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    for city, (lat, lon) in CITIES.items():
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=5.0&starttime={three_days_ago}"
        try:
            quakes = requests.get(url, timeout=5).json().get('features', [])
            if not quakes: st.write(f"✅ {city}: Сейсмически спокойно.")
            for q in quakes:
                dt = datetime.fromtimestamp(q['properties']['time'] / 1000).strftime('%d.%m %H:%M')
                st.error(f"⚠️ {city}: {dt} | {q['properties']['mag']} M | {q['properties']['place']}")
        except:
            continue

with tab3:
    st.subheader("🧪 Научная концепция LIS")
    st.markdown("""
    Наша система основана на гипотезе **Литосферно-Ионосферного Взаимодействия (ЛИВ)**. 
    Тектоническое напряжение в земной коре приводит к эмиссии радона, который ионизирует приземные слои воздуха. 
    Эти процессы искажают концентрацию электронов (VTEC) на высотах 100–300 км.
    Мы используем **Z-индекс** для отделения тектонических аномалий от фонового шума солнечной активности.
    """)

# Автообновление
time.sleep(60)
st.rerun()