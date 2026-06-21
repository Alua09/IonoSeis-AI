import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import math
import time
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard")

CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}

# Гарантированная инициализация состояний
if 'history' not in st.session_state: st.session_state.history = {city: [] for city in CITIES}
if 'archive_results' not in st.session_state: st.session_state.archive_results = []


# --- НАУЧНЫЕ ФУНКЦИИ ---
def get_space_weather_data():
    try:
        f107 = float(requests.get("https://services.swpc.noaa.gov/products/noaa-f10.7-flux-between-events.json",
                                  timeout=3).json()[-1][1])
        kp = float(
            requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=3).json()[-1][
                1])
        return kp, f107
    except:
        return 2.0, 150.0


def get_diurnal_trend(hour, lat, f107):
    base = 8.0 + (f107 / 20.0)
    diurnal = base + 15.0 * np.cos(np.pi * (hour - 14) / 12)
    return round(diurnal * (np.cos(np.radians(lat))), 1)


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")
kp, f107 = get_space_weather_data()
st.info(f"🌐 Kp: **{kp}** | ☀️ F10.7: **{f107}** | 📡 Радиус: 500 км")

tab1, tab2, tab3 = st.tabs(["🟢 Live-мониторинг", "📂 Сейсмо-архив", "📊 Анализ нормы VTEC"])

with tab1:
    # (Логика Live-мониторинга)
    try:
        url_quakes = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=" + (
                    datetime.now() - timedelta(days=1)).isoformat()
        quakes_data = requests.get(url_quakes, timeout=5).json().get('features', [])
    except:
        quakes_data = []

    for city, (lat, lon, offset) in CITIES.items():
        st.markdown("---")
        nearby = [q for q in quakes_data if math.sqrt(
            (q['geometry']['coordinates'][1] - lat) ** 2 + (q['geometry']['coordinates'][0] - lon) ** 2) < 4.5]
        hour = (datetime.now(timezone.utc) + timedelta(hours=offset)).hour
        base_norm = get_diurnal_trend(hour, lat, f107)

        col1, col2 = st.columns([1, 2])
        col1.subheader(f"📍 {city}")
        if nearby:
            col2.error(f"⚡ {nearby[0]['properties']['mag']}M | {nearby[0]['properties']['place']}")
        else:
            col2.success("✅ Сейсмика: Спокойно")

    time.sleep(5)
    st.rerun()

with tab2:
    st.subheader("📂 Архив сейсмических событий")
    with st.form(key='archive_form'):
        city_sel = st.selectbox("Город:", list(CITIES.keys()))
        date_sel = st.date_input("Дата начала:", datetime.now() - timedelta(days=7))
        submitted = st.form_submit_button("Загрузить данные")

    if submitted:
        lat, lon = CITIES[city_sel][0], CITIES[city_sel][1]
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={date_sel.isoformat()}&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=3.0"
        try:
            res = requests.get(url, timeout=10).json()
            st.session_state.archive_results = res.get('features', [])
        except:
            st.error("Ошибка загрузки.")

    if st.session_state.archive_results:
        for f in st.session_state.archive_results[:10]:
            p = f['properties']
            st.write(
                f"📅 {datetime.fromtimestamp(p['time'] / 1000).strftime('%Y-%m-%d')} | **{p['mag']} M** | {p['place']}")
    else:
        st.info("Данные не загружены. Выберите параметры и нажмите 'Загрузить данные'.")

with tab3:
    st.subheader("📊 Анализ нормы VTEC")
    c = st.selectbox("Город для анализа:", list(CITIES.keys()), key="norm_city")
    h = st.slider("Час суток (UTC):", 0, 23, 12, key="norm_hour")

    norm = get_diurnal_trend(h, CITIES[c][0], f107)
    st.metric("Ожидаемый уровень VTEC:", f"{norm} TECU")
    st.write("Этот показатель рассчитывается на основе текущего солнечного потока F10.7.")