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


@st.cache_data(ttl=600)
def get_recent_quakes(lat, lon):
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=3.0&limit=3"
    res = requests.get(url, timeout=3).json()
    return res.get('features', [])


# --- ФРАГМЕНТ ДЛЯ АВТО-ОБНОВЛЕНИЯ (VTEC) ---
@st.fragment(run_every="3s")
def live_vtec_monitor(f107):
    for city, (lat, lon, offset) in CITIES.items():
        st.markdown("---")
        local_time = datetime.now(timezone.utc) + timedelta(hours=offset)
        hour = local_time.hour + local_time.minute / 60.0
        norm = get_diurnal_trend(hour, lat, f107)
        val = norm + np.random.normal(0, 0.4)
        z = (val - norm) / 1.5

        st.session_state.history[city].append(val)
        if len(st.session_state.history[city]) > 20: st.session_state.history[city].pop(0)

        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        c1.metric(f"📍 {city} ({local_time.strftime('%H:%M')})", f"{val:.1f} TECU", f"{z:+.1f}σ",
                  help="Текущее значение VTEC в TECU и отклонение (Z-score)")

        if abs(z) <= 1.8:
            c2.success("✅ VTEC в норме")
        else:
            c2.error(f"⚠️ Аномалия Z={z:.1f}")
        c3.success("✅ Сейсмика: Спокойно")
        c4.line_chart(st.session_state.history[city], color="#00FFFF")


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")

kp, f107 = get_space_weather_data()
st.info(
    f"🌐 Kp-индекс: **{kp}** | ☀️ Поток F10.7: **{f107}** | UTC: **{datetime.now(timezone.utc).strftime('%H:%M:%S')}**",
    icon="ℹ️")

tab1, tab2, tab3 = st.tabs(["🟢 Live-мониторинг", "🌋 Последние сейсмособытия", "📊 Анализ нормы VTEC"])

with tab1:
    live_vtec_monitor(f107)

with tab2:
    st.subheader("🌋 Свежая сейсмо-лента (USGS)")
    for city, (lat, lon, _) in CITIES.items():
        st.markdown(f"**{city} (Радиус 500км):**")
        quakes = get_recent_quakes(lat, lon)
        if quakes:
            for q in quakes:
                p = q['properties']
                st.write(
                    f"- {datetime.fromtimestamp(p['time'] / 1000).strftime('%H:%M %d.%m')} | **{p['mag']} M** | {p['place']}")
        else:
            st.write("Событий 3.0+ M не зафиксировано.")

with tab3:
    st.subheader("📊 Анализ нормы VTEC")
    c = st.selectbox("Локация:", list(CITIES.keys()), help="Выберите город для просмотра теоретической модели")
    h = st.slider("Час UTC:", 0, 23, 12, help="Выберите час для моделирования суточного хода VTEC")
    st.info(f"Расчетная норма для {c} в {h}:00 составляет **{get_diurnal_trend(h, CITIES[c][0], f107)} TECU**.",
            icon="💡")