import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import time
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard")

CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}

if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}


# --- ФУНКЦИИ ---
def get_space_weather():
    try:
        f107 = float(requests.get("https://services.swpc.noaa.gov/products/noaa-f10.7-flux-between-events.json",
                                  timeout=3).json()[-1][1])
        kp = float(
            requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=3).json()[-1][
                1])
        return kp, f107
    except:
        return 2.0, 150.0


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")
tab1, tab2 = st.tabs(["🟢 Мониторинг (Live)", "📂 Архив сейсмических данных"])

with tab1:
    kp, f107 = get_space_weather()
    st.info(f"🌐 Kp-индекс: {kp} | ☀️ F10.7: {f107}")

    for city, (lat, lon, offset) in CITIES.items():
        val = 10 + np.random.normal(0, 1)
        st.session_state.history[city].append(val)
        if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

        col1, col2 = st.columns([1, 3])
        col1.metric(f"📍 {city}", f"{val:.1f} VTEC")
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='cyan')
        ax.axis('off')
        col2.pyplot(fig)
    time.sleep(2)
    st.rerun()

with tab2:
    st.subheader("Поиск архивных сейсмических данных")
    with st.form("archive"):
        city_sel = st.selectbox("Город:", list(CITIES.keys()))
        date_sel = st.date_input("Дата начала:", datetime.now() - timedelta(days=7))
        submit = st.form_submit_button("Найти события")

    if submit:
        lat, lon = CITIES[city_sel][0], CITIES[city_sel][1]
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={date_sel.isoformat()}&endtime={(date_sel + timedelta(days=30)).isoformat()}&latitude={lat}&longitude={lon}&maxradiuskm=1000&minmagnitude=2.0"

        try:
            data = requests.get(url, timeout=10).json()
            features = data.get('features', [])
            st.write(f"Найдено событий: **{len(features)}**")
            for f in features[:10]:
                p = f['properties']
                st.write(
                    f"📅 {datetime.fromtimestamp(p['time'] / 1000).strftime('%Y-%m-%d %H:%M')} | 📍 {p['place']} | ⚡ Магнитуда: **{p['mag']}**")
        except Exception as e:
            st.error(f"Ошибка загрузки: {e}")