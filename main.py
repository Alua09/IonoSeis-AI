import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import math
import time
import streamlit.components.v1 as components
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
if 'archive_results' not in st.session_state:
    st.session_state.archive_results = None


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
st.info(f"🌐 Kp: **{kp}** | ☀️ F10.7: **{f107}** | 📡 Радиус поиска: 500 км")

tab1, tab2 = st.tabs(["🟢 Мониторинг (Live)", "📂 Архив землетрясений"])

with tab1:
    # Запрос данных (раз в 30 секунд для экономии ресурсов)
    try:
        url_quakes = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=" + (
                    datetime.now() - timedelta(days=1)).isoformat()
        quakes_data = requests.get(url_quakes, timeout=5).json().get('features', [])
    except:
        quakes_data = []

    for city, (lat, lon, offset) in CITIES.items():
        st.markdown("---")
        local_time = datetime.now(timezone.utc) + timedelta(hours=offset)
        hour = local_time.hour + local_time.minute / 60.0

        # Сейсмика: 500 км ~ 4.5 градуса
        nearby = [q for q in quakes_data if math.sqrt(
            (q['geometry']['coordinates'][1] - lat) ** 2 + (q['geometry']['coordinates'][0] - lon) ** 2) < 4.5]

        base_norm = get_diurnal_trend(hour, lat, f107)
        val = base_norm + np.random.normal(0, 0.8 + (kp * 0.1))

        st.session_state.history[city].append(val)
        if len(st.session_state.history[city]) > 60: st.session_state.history[city].pop(0)

        # Более строгий расчет Z-score
        z = (val - base_norm) / (1.5 + (kp * 0.3))
        is_anomaly = abs(z) > 1.8  # Увеличили порог, чтобы меньше «шумело»

        col1, col2, col3, col4 = st.columns([1, 1, 1.5, 2])
        col1.subheader(f"📍 {city}")
        col1.caption(f"🕒 {local_time.strftime('%H:%M:%S')}")
        col2.metric("VTEC", f"{val:.1f}", f"{z:+.1f}σ")

        if is_anomaly:
            col3.error(f"⚠️ АНОМАЛИЯ (Z={z:.1f})")
        else:
            col3.success(f"✅ Стабильно (Z={z:.1f})")

        if nearby:
            q = nearby[0]['properties']
            col3.write(f"⚡ **{q['mag']}M** | {q['place'].split(',')[-1]}")
        else:
            col3.write("✅ Сейсмика: Спокойно")

        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='red' if is_anomaly else 'cyan', lw=2)
        ax.axis('off')
        col4.pyplot(fig)

    time.sleep(8)  # Увеличили интервал до 8 секунд для плавности
    st.rerun()

with tab2:
    # Архив остается неизменным, так как он надежен
    st.subheader("Поиск архивных данных (USGS)")
    with st.form(key='archive_form'):
        city_sel = st.selectbox("Выберите город:", list(CITIES.keys()))
        date_sel = st.date_input("Дата:", datetime.now() - timedelta(days=7))
        submitted = st.form_submit_button("Найти")

    if submitted:
        lat, lon = CITIES[city_sel][0], CITIES[city_sel][1]
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={date_sel.isoformat()}&endtime={(date_sel + timedelta(days=30)).isoformat()}&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=2.0"
        try:
            res = requests.get(url, timeout=10).json()
            st.session_state.archive_results = res.get('features', [])
        except:
            st.error("Ошибка сети.")

    if st.session_state.archive_results is not None:
        for f in st.session_state.archive_results[:10]:
            p = f['properties']
            st.error(
                f"⚠️ {datetime.fromtimestamp(p['time'] / 1000).strftime('%Y-%m-%d')} | **{p['mag']} M** | {p['place']}")