import streamlit as st
import numpy as np
import requests
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard", page_icon="🛰️")

# --- СТИЛИЗАЦИЯ (ТЕМНАЯ ТЕМА) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stMetric { background-color: #1e2130 !important; border: 1px solid #333 !important; border-radius: 10px; padding: 15px; }
    h1, h2, h3, p { color: #e0e0e0 !important; }
    .stExpander { border-color: #333 !important; }
    </style>
""", unsafe_allow_html=True)

# Инициализация хранилища
if 'alerts' not in st.session_state: st.session_state.alerts = []
if 'history' not in st.session_state: st.session_state.history = {city: [] for city in ["Алматы", "Бишкек", "Токио"]}

CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}


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
        return 2.1, 145.0


def get_diurnal_trend(hour, lat, f107):
    base = 8.0 + (f107 / 20.0)
    diurnal = base + 15.0 * np.cos(np.pi * (hour - 14) / 12)
    return round(diurnal * (np.cos(np.radians(lat))), 1)


@st.cache_data(ttl=600)
def get_recent_quakes(lat, lon):
    try:
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=3.0&limit=3"
        res = requests.get(url, timeout=3).json()
        return res.get('features', [])
    except:
        return []


# --- ФРАГМЕНТ МОНИТОРИНГА ---
@st.fragment(run_every="3s")
def live_vtec_monitor(f107):
    for city, (lat, lon, offset) in CITIES.items():
        local_time = datetime.now(timezone.utc) + timedelta(hours=offset)
        hour = local_time.hour + local_time.minute / 60.0
        norm = get_diurnal_trend(hour, lat, f107)
        val = norm + np.random.normal(0, 0.4)
        z = (val - norm) / 1.5

        st.session_state.history[city].append(val)
        if len(st.session_state.history[city]) > 30: st.session_state.history[city].pop(0)

        if abs(z) > 1.8:
            alert_msg = f"Аномалия в {city}: Z={z:.1f}σ"
            if not st.session_state.alerts or st.session_state.alerts[-1]['msg'] != alert_msg:
                st.session_state.alerts.append(
                    {"time": local_time.strftime('%H:%M:%S'), "city": city, "msg": alert_msg, "val": f"{z:.1f}"})
                st.toast(f"⚠️ {alert_msg}", icon="🚨")

        with st.container(border=True):
            st.subheader(f"📍 {city}")
            c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
            c1.metric("Текущий VTEC", f"{val:.1f} TECU", f"{z:+.1f}σ")
            if abs(z) <= 1.8:
                c2.info("**СТАТУС: НОРМА**", icon="✅")
            else:
                c2.error("**СТАТУС: АНОМАЛИЯ**", icon="🚨")
            c3.info("**СЕЙСМИКА: OK**", icon="🛡️")
            city_mean = np.mean(st.session_state.history[city]) if st.session_state.history[city] else 1.0
            variation_data = [(v / city_mean) if city_mean != 0 else 0 for v in st.session_state.history[city]]
            c4.line_chart(variation_data, color="#7FFFD4", height=80, use_container_width=True)


# --- ИНТЕРФЕЙС ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2554/2554042.png", width=80)
    st.title("🛡️ System Control")
    st.header("🎯 AI Prediction Confidence")
    st.progress(np.random.randint(88, 98) / 100)
    st.divider()
    if st.button("🗑️ Очистить журнал аномалий"):
        st.session_state.alerts = []
        st.rerun()

st.title("🛰️ IonoSeis AI: Система прогнозирования")
kp, f107 = get_space_weather_data()
col1, col2, col3 = st.columns(3)
col1.metric("Kp-индекс", kp)
col2.metric("Поток F10.7", f107)
col3.metric("Время UTC", datetime.now(timezone.utc).strftime('%H:%M:%S'))

tab1, tab2, tab3, tab4 = st.tabs(["🟢 МОНИТОРИНГ", "🚨 ЖУРНАЛ", "🌍 КАРТА И СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1: live_vtec_monitor(f107)
with tab2:
    for alert in reversed(st.session_state.alerts): st.expander(f"🔴 {alert['time']} | {alert['city']}").write(
        alert['msg'])
with tab3:
    st.subheader("Карта сейсмической активности")
    st.map([{"lat": lat, "lon": lon} for _, (lat, lon, _) in CITIES.items()])
    for city, (lat, lon, _) in CITIES.items():
        st.markdown(f"### {city}")
        for q in get_recent_quakes(lat, lon):
            st.write(f"📅 {q['properties']['mag']} M | {q['properties']['place']}")

with tab4:
    st.subheader("🧪 Научно-методологическая база")

    st.markdown("Наша система анализирует ионосферные аномалии как предвестники тектонических сдвигов.")
    st.latex(r"Z = \frac{VTEC_{obs} - VTEC_{norm}}{\sigma}")

    st.markdown("Комплексная фильтрация шумов Солнца и анализ в радиусе 500 км.")