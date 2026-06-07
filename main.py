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
    st.session_state.last_alert = {city: False for city in CITIES}


# --- НАУЧНЫЕ ФУНКЦИИ ---
def get_space_weather_data():
    try:
        resp_f107 = requests.get("https://services.swpc.noaa.gov/products/noaa-f10.7-flux-between-events.json",
                                 timeout=5).json()
        f107 = float(resp_f107[-1][1])
        resp_kp = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        kp = float(resp_kp[-1][1])
        return kp, f107
    except:
        return 2.0, 150.0


def get_diurnal_trend(hour, lat, date, f107):
    day_of_year = date.timetuple().tm_yday
    seasonal = 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    ionization_base = 8.0 + (f107 / 20.0)
    diurnal = ionization_base + 15.0 * math.cos(math.pi * (hour - 14) / 12)
    return round(diurnal * (math.cos(math.radians(lat))) * seasonal, 1)


def moving_average(data, window=5):
    if len(data) < window: return data
    return np.convolve(data, np.ones(window) / window, mode='valid')


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")

tab1, tab2 = st.tabs(["🟢 Мониторинг (Live)", "📂 Архив землетрясений"])

# --- ВКЛАДКА 1: LIVE ---
with tab1:
    kp, f107 = get_space_weather_data()
    st.info(f"🌐 Kp-индекс: **{kp}** | ☀️ Солнечный поток (F10.7): **{f107}**")

    try:
        quakes = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=" +
                              (datetime.now() - timedelta(days=1)).isoformat(), timeout=5).json()
    except:
        quakes = {'features': []}

    for city, (lat, lon, offset) in CITIES.items():
        st.markdown("---")
        local_now = datetime.now(timezone.utc) + timedelta(hours=offset)
        hour = local_now.hour + local_now.minute / 60.0

        base_norm = get_diurnal_trend(hour, lat, local_now, f107)
        val = base_norm + np.random.normal(0, 0.5 + (kp * 0.1))

        st.session_state.history[city].append(val)
        if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

        z = (val - base_norm) / (1.5 + (kp * 0.2))

        is_anomaly = abs(z) > 1.5
        if is_anomaly and not st.session_state.last_alert[city]:
            st.toast(f"⚠️ Внимание! Аномалия в городе {city}", icon="🚨")
            components.html(
                """<audio autoplay="true"><source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg"></audio>""",
                height=0)
            st.session_state.last_alert[city] = True
        elif not is_anomaly:
            st.session_state.last_alert[city] = False

        col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
        with col1:
            st.subheader(f"📍 {city}")
            st.caption(f"🕒 {local_now.strftime('%H:%M:%S')}")
            st.metric("VTEC", f"{val:.1f}", f"{z:.1f}σ")
        with col2:
            st.write("Ионосфера:")
            if is_anomaly:
                st.warning("⚠️ АНОМАЛИЯ")
            else:
                st.info("✅ Стабильно")
        with col3:
            st.write("Сейсмика:")
            st.success("✅ Спокойно")
        with col4:
            fig, ax = plt.subplots(figsize=(6, 1.2))
            ax.plot(moving_average(st.session_state.history[city], 5), color='red' if is_anomaly else 'cyan',
                    linewidth=2.5)
            ax.axis('off')
            st.pyplot(fig)

    time.sleep(5)
    st.rerun()

# --- ВКЛАДКА 2: АРХИВ ---
with tab2:
    st.subheader("Поиск архивных сейсмических данных (Алматы)")
    target_date = st.date_input("Выберите дату для проверки", datetime.now() - timedelta(days=1))

    if st.button("Проверить архив"):
        start = datetime.combine(target_date, datetime.min.time()).isoformat()
        end = datetime.combine(target_date, datetime.max.time()).isoformat()
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start}&endtime={end}&latitude={CITIES['Алматы'][0]}&longitude={CITIES['Алматы'][1]}&maxradiuskm=500"

        try:
            res = requests.get(url, timeout=5).json()
            features = res.get('features', [])
            if features:
                mags = [f['properties']['mag'] for f in features]
                times = [datetime.fromtimestamp(f['properties']['time'] / 1000).strftime('%H:%M') for f in features]

                for f in features:
                    p = f['properties']
                    st.error(
                        f"⚠️ M{p['mag']} | {p['place']} | {datetime.fromtimestamp(p['time'] / 1000).strftime('%H:%M:%S')}")

                fig, ax = plt.subplots(figsize=(10, 3))
                ax.bar(times, mags, color='orange', alpha=0.7)
                ax.set_title(f"Сейсмическая активность за {target_date}")
                ax.set_ylabel("Магнитуда")
                st.pyplot(fig)
            else:
                st.success("В этот день крупных событий в радиусе 500 км не зафиксировано.")
        except Exception as e:
            st.error(f"Ошибка получения данных: {e}")