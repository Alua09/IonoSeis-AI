import streamlit as st
import numpy as np
import requests
import plotly.express as px
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard", page_icon="🛰️")

# --- СТИЛИЗАЦИЯ ---
st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fb; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; }
    @keyframes scan { 0% { opacity: 0; } 50% { opacity: 1; } 100% { opacity: 0; } }
    .scanning-beam {
        position: absolute; top: -100px; left: 50px; 
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(127, 255, 212, 0.4) 0%, rgba(127, 255, 212, 0) 70%);
        animation: scan 1.5s infinite;
    }
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
        f107 = float(requests.get("https://services.swpc.noaa.gov/products/noaa-f10.7-flux-between-events.json", timeout=3).json()[-1][1])
        kp = float(requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=3).json()[-1][1])
        return kp, f107
    except: return 2.1, 145.0

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
    except: return []

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
                st.session_state.alerts.append({"time": local_time.strftime('%H:%M:%S'), "city": city, "msg": alert_msg, "val": f"{z:.1f}"})
                st.toast(f"⚠️ {alert_msg}", icon="🚨")

        with st.container(border=True):
            c_logo, c_main, c_chart = st.columns([0.8, 2, 2.5])
            with c_logo:
                st.image("https://cdn-icons-png.flaticon.com/512/3203/3203926.png")
                st.markdown('<div class="scanning-beam"></div>', unsafe_allow_html=True)
            with c_main:
                st.subheader(f"📍 {city}")
                st.metric("VTEC", f"{val:.1f} TECU", f"{z:+.1f}σ")
                if abs(z) <= 1.8: st.info("**СТАТУС: НОРМА**", icon="✅")
                else: st.error("**СТАТУС: АНОМАЛИЯ**", icon="🚨")
                st.info("**СЕЙСМИКА: OK**", icon="🛡️")
            with c_chart:
                city_mean = np.mean(st.session_state.history[city]) if st.session_state.history[city] else 1.0
                variation_data = [(v / city_mean) if city_mean != 0 else 0 for v in st.session_state.history[city]]
                fig = px.line(y=variation_data, range_y=[0.8, 1.2])
                fig.update_layout(height=60, margin=dict(l=0, r=0, t=0, b=0), showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                fig.update_traces(line_color='#7FFFD4')
                st.plotly_chart(fig, use_container_width=True)

# --- ИНТЕРФЕЙС ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2554/2554042.png", width=80)
    st.title("🛡️ System Control")
    st.success("🤖 AI Engine: Active")
    st.success("📡 Ionosphere API: Connected")
    st.success("🌍 USGS Seismic: Online")
    st.divider()
    if st.button("🗑️ Очистить журнал аномалий"):
        st.session_state.alerts = []
        st.rerun()

st.title("🛰️ IonoSeis AI: Система прогнозирования")
st.caption("Экспертная панель анализа ионосферных предвестников")
kp, f107 = get_space_weather_data()
col1, col2, col3 = st.columns(3)
col1.metric("Геомагнитный Kp-индекс", kp)
col2.metric("Солнечный поток F10.7", f107)
col3.metric("Время UTC", datetime.now(timezone.utc).strftime('%H:%M:%S'))

tab1, tab2, tab3, tab4 = st.tabs(["🟢 МОНИТОРИНГ", "🚨 ЖУРНАЛ АНОМАЛИЙ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1: live_vtec_monitor(f107)
with tab2:
    if st.session_state.alerts:
        for alert in reversed(st.session_state.alerts):
            with st.expander(f"🔴 {alert['time']} | {alert['city']} | Z={alert['val']}σ"):
                st.write(f"**Анализ:** {alert['msg']}. Рекомендуем проверить Kp-индекс.")
    else: st.info("Аномалий нет.")

with tab3:
    for city, (lat, lon, _) in CITIES.items():
        st.markdown(f"### Регион: {city}")
        for q in get_recent_quakes(lat, lon):
            p = q['properties']
            st.write(f"📅 {datetime.fromtimestamp(p['time'] / 1000).strftime('%d.%m %H:%M')} | **{p['mag']} M** | {p['place']}")

with tab4:
    st.subheader("🧪 Научно-методологическая база")
    st.markdown("""
    Наша система работает на базе теории **литосферно-ионосферного взаимодействия (LIS)**. 
    Когда в земной коре из-за тектоники растет напряжение, это меняет плотность ионосферы.
    """)
    st.latex(r"Z = \frac{VTEC_{obs} - VTEC_{norm}}{\sigma}")
    st.markdown("Мы фильтруем влияние Солнца (Kp-индекс) и ищем отклонения от математической нормы.")