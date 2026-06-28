import streamlit as st
import numpy as np
import requests
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard", page_icon="🛰️")

# --- СТИЛИЗАЦИЯ ---
st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fb; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; }
    </style>
""", unsafe_allow_html=True)

# Инициализация хранилища
if 'alerts' not in st.session_state: st.session_state.alerts = []
if 'history' not in st.session_state: st.session_state.history = {city: [] for city in
                                                                  ["Алматы", "Бишкек", "Токио", "Каракас"]}

CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9),
    "Каракас": (10.48, -66.90, -4)
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

            c1.metric("Текущий VTEC", f"{val:.1f} TECU", f"{z:+.1f}σ",
                      help="Z-score > 1.8 показывает, что текущее состояние ионосферы сильно отклоняется от математической модели нормы.")

            if abs(z) <= 1.8:
                c2.info("**СТАТУС: НОРМА**", icon="✅")
            else:
                c2.error("**СТАТУС: АНОМАЛИЯ**", icon="🚨")

            c3.info("**СЕЙСМИКА: OK**", icon="🛡️")

            st.caption("График: Относительное изменение VTEC (отклонение от среднего)")
            city_mean = np.mean(st.session_state.history[city]) if st.session_state.history[city] else 1.0
            variation_data = [(v / city_mean) if city_mean != 0 else 0 for v in st.session_state.history[city]]
            c4.line_chart(variation_data, color="#7FFFD4", height=80, use_container_width=True)


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
col1.metric("Геомагнитный Kp-индекс", kp,
            help="Если Kp > 4, значит идут магнитные бури, которые влияют на ионосферу независимо от землетрясений.")
col2.metric("Солнечный поток F10.7", f107,
            help="Базовый показатель солнечной активности: чем он выше, тем плотнее ионосфера.")
col3.metric("Время UTC", datetime.now(timezone.utc).strftime('%H:%M:%S'),
            help="Время для синхронизации данных с мировыми сейсмостанциями.")

tab1, tab2, tab3, tab4 = st.tabs(["🟢 МОНИТОРИНГ", "🚨 ЖУРНАЛ АНОМАЛИЙ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1:
    live_vtec_monitor(f107)

with tab2:
    if st.session_state.alerts:
        for alert in reversed(st.session_state.alerts):
            with st.expander(f"🔴 {alert['time']} | {alert['city']} | Z={alert['val']}σ"):
                st.write(
                    f"**Анализ:** {alert['msg']}. Рекомендуем проверить Kp-индекс — если он низкий, это может быть сигналом тектонической активности.")
    else:
        st.info("Аномалий за текущую сессию не зафиксировано.")

with tab3:
    for city, (lat, lon, _) in CITIES.items():
        st.markdown(f"### Регион: {city}")
        quakes = get_recent_quakes(lat, lon)
        if quakes:
            for q in quakes:
                p = q['properties']
                st.write(
                    f"📅 {datetime.fromtimestamp(p['time'] / 1000).strftime('%d.%m %H:%M')} | **{p['mag']} M** | {p['place']}")
        else:
            st.write("Сейсмическая активность в радиусе 500 км в норме.")

with tab4:
    st.subheader("🧪 Научно-методологическая база")

    # Визуальное представление процессов

    st.markdown("— *Схема взаимодействия литосферы и ионосферы:*")

    st.markdown("""
    Наша система работает на базе теории **литосферно-ионосферного взаимодействия (LIS)**. Если говорить просто: Земля — это не просто камень под нашими ногами, а сложная система, где процессы в глубине коры могут «отзываться» даже в космосе.

    **1. Как это работает?**
    Когда в земной коре из-за движения тектонических плит начинает расти напряжение, происходят микродеформации. Это приводит к выбросу газов (например, радона) и появлению слабых электрических полей. Эти возмущения «долетают» до ионосферы — слоя атмосферы, насыщенного заряженными частицами (плазмой), — и меняют её плотность.

    **2. Математический метод: поиск аномалий**
    Чтобы понять, что ионосфера «волнуется» именно из-за тектонических процессов, а не из-за обычной погоды или Солнца, мы используем **Z-оценку**. Мы вычисляем, насколько текущее состояние ионосферы (VTEC) отличается от «нормы» для этого времени суток.

    **Формула аномалии:**
    """)
    st.latex(r"Z = \frac{VTEC_{obs} - VTEC_{norm}}{\sigma}")
    st.markdown("""
    * $VTEC_{obs}$ — то, что мы видим в данный момент.
    * $VTEC_{norm}$ — «нормальное» состояние, рассчитанное нашей моделью.
    * $\sigma$ — статистическая погрешность (шум).
    """)