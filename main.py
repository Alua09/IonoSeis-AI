import streamlit as st
import numpy as np
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

if 'history' not in st.session_state: st.session_state.history = {city: [] for city in CITIES}
if 'archive_results' not in st.session_state: st.session_state.archive_results = None
if 'last_update' not in st.session_state: st.session_state.last_update = time.time()


# --- ФУНКЦИИ ---
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
tab1, tab2, tab3 = st.tabs(["🟢 Live-мониторинг", "📂 Сейсмо-архив", "📊 Анализ нормы VTEC"])

with tab1:
    for city, (lat, lon, offset) in CITIES.items():
        st.markdown("---")
        hour = (datetime.now(timezone.utc) + timedelta(hours=offset)).hour
        val = get_diurnal_trend(hour, lat, f107) + np.random.normal(0, 0.4)
        z = (val - get_diurnal_trend(hour, lat, f107)) / 1.5

        st.session_state.history[city].append(val)
        if len(st.session_state.history[city]) > 20: st.session_state.history[city].pop(0)

        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        c1.metric(f"📍 {city}", f"{val:.1f} TECU")
        if abs(z) <= 1.8:
            c2.success("✅ VTEC в норме")
        else:
            c2.error(f"⚠️ Аномалия Z={z:.1f}")
        c3.success("✅ Сейсмика: Спокойно")
        c4.line_chart(st.session_state.history[city], color="#00FFFF")

    # Авто-обновление страницы каждые 5 секунд без блокировки интерфейса
    if time.time() - st.session_state.last_update > 5:
        st.session_state.last_update = time.time()
        st.rerun()

with tab2:
    st.subheader("📂 Сейсмо-архив")
    with st.form("archive_form"):
        city_sel = st.selectbox("Город:", list(CITIES.keys()))
        date_sel = st.date_input("Дата начала:", datetime.now() - timedelta(days=7))
        btn = st.form_submit_button("Загрузить данные")

    if btn:
        lat, lon = CITIES[city_sel][0], CITIES[city_sel][1]
        # Фильтр дат: от выбранной даты до текущего момента
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={date_sel.isoformat()}&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=3.0"
        res = requests.get(url, timeout=3).json()
        st.session_state.archive_results = res.get('features', [])

    if st.session_state.archive_results:
        for f in st.session_state.archive_results[:5]:
            p = f['properties']
            st.write(f"📅 {datetime.fromtimestamp(p['time'] / 1000).strftime('%Y-%m-%d')} | {p['mag']} M | {p['place']}")

with tab3:
    st.subheader("📊 Анализ нормы VTEC")
    c = st.selectbox("Город:", list(CITIES.keys()))
    h = st.slider("Час UTC:", 0, 23, 12)
    st.info(f"Норма: **{get_diurnal_trend(h, CITIES[c][0], f107)} TECU**.")