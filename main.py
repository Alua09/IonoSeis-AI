import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
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

# Инициализация состояния
if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}
if 'last_alert' not in st.session_state:
    st.session_state.last_alert = {city: False for city in CITIES}
if 'archive_results' not in st.session_state:
    st.session_state.archive_results = None


# --- НАУЧНЫЕ ФУНКЦИИ ---
def get_space_weather_data():
    try:
        resp_f107 = requests.get("https://services.swpc.noaa.gov/products/noaa-f10.7-flux-between-events.json",
                                 timeout=3).json()
        f107 = float(resp_f107[-1][1])
        resp_kp = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=3).json()
        kp = float(resp_kp[-1][1])
        return kp, f107
    except:
        return 2.0, 150.0


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")
tab1, tab2 = st.tabs(["🟢 Мониторинг (Live)", "📂 Архив землетрясений"])

with tab1:
    kp, f107 = get_space_weather_data()
    st.info(f"🌐 Kp: {kp} | ☀️ F10.7: {f107}")

    for city, (lat, lon, offset) in CITIES.items():
        st.markdown("---")
        local_time = datetime.now(timezone.utc) + timedelta(hours=offset)

        # Генерация данных
        val = 20 + (f107 / 10) + np.random.normal(0, 1 + (kp * 0.2))
        st.session_state.history[city].append(val)
        if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

        is_anomaly = val > 35 + (kp * 2)
        if is_anomaly and not st.session_state.last_alert[city]:
            st.toast(f"⚠️ Аномалия в {city}!", icon="🚨")
            components.html(
                """<audio autoplay="true"><source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg"></audio>""",
                height=0)
            st.session_state.last_alert[city] = True
        elif not is_anomaly:
            st.session_state.last_alert[city] = False

        col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
        col1.subheader(f"📍 {city}")
        col1.caption(f"🕒 {local_time.strftime('%H:%M:%S')}")
        col2.metric("VTEC", f"{val:.1f}")
        col3.write("Статус: " + ("⚠️ АНОМАЛИЯ" if is_anomaly else "✅ Стабильно"))

        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='red' if is_anomaly else 'cyan', lw=2)
        ax.axis('off')
        col4.pyplot(fig)

    time.sleep(3)
    st.rerun()

with tab2:
    st.subheader("Поиск архивных данных (USGS)")
    with st.form(key='archive_search'):
        city_sel = st.selectbox("Выберите город:", list(CITIES.keys()))
        date_sel = st.date_input("Дата:", datetime.now() - timedelta(days=7))
        submit_button = st.form_submit_button(label='Проверить архив')

    if submit_button:
        lat, lon = CITIES[city_sel][0], CITIES[city_sel][1]
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={date_sel.isoformat()}&endtime={(date_sel + timedelta(days=30)).isoformat()}&latitude={lat}&longitude={lon}&maxradiuskm=1000&minmagnitude=3.0"
        try:
            res = requests.get(url, timeout=10).json()
            st.session_state.archive_results = res.get('features', [])
        except:
            st.error("Ошибка связи с сервером USGS.")

    if st.session_state.archive_results is not None:
        if st.session_state.archive_results:
            for f in st.session_state.archive_results:
                p = f['properties']
                dt = datetime.fromtimestamp(p['time'] / 1000).strftime('%Y-%m-%d %H:%M')
                st.error(f"⚠️ {dt} | **{p['mag']} M** | {p['place']}")
        else:
            st.success("Крупных землетрясений не найдено.")