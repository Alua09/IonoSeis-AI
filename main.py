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
st.info(f"🌐 Kp: **{kp}** | ☀️ F10.7: **{f107}** | 📡 Радиус поиска: 500 км")

tab1, tab2, tab3 = st.tabs(["🟢 Live-мониторинг", "📂 Сейсмо-архив", "📊 Анализ нормы VTEC"])

with tab1:
    # Используем placeholder для обновления без st.rerun()
    live_placeholder = st.empty()

    while True:
        with live_placeholder.container():
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
                val = base_norm + np.random.normal(0, 0.8 + (kp * 0.1))

                st.session_state.history[city].append(val)
                if len(st.session_state.history[city]) > 60: st.session_state.history[city].pop(0)

                z = (val - base_norm) / (1.5 + (kp * 0.3))
                is_anomaly = abs(z) > 1.8

                col1, col2, col3, col4 = st.columns([1, 1, 1.5, 2])
                col1.subheader(f"📍 {city}")
                col1.metric("VTEC", f"{val:.1f}", f"{z:+.1f}σ")

                if is_anomaly:
                    col2.error(f"⚠️ АНОМАЛИЯ (Z={z:.1f})")
                else:
                    col2.success(f"✅ Стабильно (Z={z:.1f})")

                if nearby:
                    q = nearby[0]['properties']
                    col2.write(f"🚨 **{q['mag']}M** | {q['place'].split(',')[-1]}")
                else:
                    col2.write("✅ Сейсмика: Спокойно")

                fig, ax = plt.subplots(figsize=(6, 1))
                ax.plot(st.session_state.history[city], color='red' if is_anomaly else 'cyan', lw=2)
                ax.axis('off')
                col4.pyplot(fig)

        time.sleep(8)

with tab2:
    st.subheader("🔍 Глубокий поиск по архиву USGS")
    with st.form(key='archive_form'):
        city_sel = st.selectbox("Город:", list(CITIES.keys()))
        mag_min = st.slider("Мин. магнитуда:", 2.0, 8.0, 3.0)
        date_sel = st.date_input("Дата начала:", datetime.now() - timedelta(days=30))
        submitted = st.form_submit_button("Начать поиск")

    if submitted:
        lat, lon = CITIES[city_sel][0], CITIES[city_sel][1]
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={date_sel.isoformat()}&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude={mag_min}"
        try:
            res = requests.get(url, timeout=10).json()
            st.session_state.archive_results = res.get('features', [])
        except:
            st.error("Ошибка сети.")

    if st.session_state.archive_results:
        st.success(f"Найдено событий: {len(st.session_state.archive_results)}")
        for f in st.session_state.archive_results[:15]:
            p = f['properties']
            st.write(
                f"📅 {datetime.fromtimestamp(p['time'] / 1000).strftime('%Y-%m-%d %H:%M')} | ⚡ **{p['mag']} M** | 📍 {p['place']}")

with tab3:
    st.subheader("📊 Анализ суточной нормы")
    c = st.selectbox("Город для проверки:", list(CITIES.keys()))
    h = st.slider("Час суток (UTC):", 0, 23, 12)
    norm = get_diurnal_trend(h, CITIES[c][0], 150.0)
    st.info(f"Для города {c} в {h}:00 UTC ожидаемый уровень VTEC составляет **{norm} TECU**.")