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

# --- ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ (САМОЕ ВАЖНОЕ) ---
if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}
if 'last_alert' not in st.session_state:
    st.session_state.last_alert = {city: False for city in CITIES}


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


def get_diurnal_trend(hour, lat, f107):
    ionization_base = 8.0 + (f107 / 20.0)
    diurnal = ionization_base + 15.0 * np.cos(np.pi * (hour - 14) / 12)
    return round(diurnal * (np.cos(np.radians(lat))), 1)


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")
tab1, tab2 = st.tabs(["🟢 Мониторинг (Live)", "📂 Архив землетрясений"])

with tab1:
    kp, f107 = get_space_weather_data()
    st.info(f"🌐 Kp: {kp} | ☀️ F10.7: {f107}")

    for city, (lat, lon, offset) in CITIES.items():
        local_time = datetime.now(timezone.utc) + timedelta(hours=offset)
        hour = local_time.hour + local_time.minute / 60.0

        base_norm = get_diurnal_trend(hour, lat, f107)
        val = base_norm + np.random.normal(0, 0.5 + (kp * 0.1))

        # Обновление истории
        st.session_state.history[city].append(val)
        if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

        z = (val - base_norm) / 1.5
        is_anomaly = abs(z) > 1.5

        # Логика алертов
        if is_anomaly and not st.session_state.last_alert[city]:
            st.toast(f"⚠️ Аномалия в {city}!", icon="🚨")
            st.session_state.last_alert[city] = True
        elif not is_anomaly:
            st.session_state.last_alert[city] = False

        col1, col2, col3 = st.columns([1, 1, 2])
        col1.metric(f"📍 {city}", f"{val:.1f} VTEC", f"{z:.1f}σ")
        col2.write("Статус: " + ("⚠️ АНОМАЛИЯ" if is_anomaly else "✅ Стабильно"))

        fig, ax = plt.subplots(figsize=(5, 1))
        ax.plot(st.session_state.history[city], color='red' if is_anomaly else 'cyan')
        ax.set_ylim(0, 50)
        ax.axis('off')
        col3.pyplot(fig)

    time.sleep(3)
    st.rerun()

with tab2:
    st.subheader("Поиск архивных данных")
    with st.form("archive_form"):
        city_sel = st.selectbox("Город:", list(CITIES.keys()))
        date_sel = st.date_input("Дата начала:", datetime.now() - timedelta(days=7))
        submitted = st.form_submit_button("Найти события")

    if submitted:
        lat, lon = CITIES[city_sel][0], CITIES[city_sel][1]
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={date_sel.isoformat()}&endtime={(date_sel + timedelta(days=30)).isoformat()}&latitude={lat}&longitude={lon}&maxradiuskm=1000&minmagnitude=2.0"

        try:
            res = requests.get(url, timeout=10).json()
            features = res.get('features', [])
            if features:
                for f in features[:10]:
                    p = f['properties']
                    st.write(
                        f"📅 {datetime.fromtimestamp(p['time'] / 1000).strftime('%Y-%m-%d')} | 📍 {p['place']} | ⚡ {p['mag']} M")
            else:
                st.write("Событий не найдено.")
        except Exception as e:
            st.error(f"Ошибка загрузки: {e}")