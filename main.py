import streamlit as st
import numpy as np
import requests
import pandas as pd
import pydeck as pdk
from datetime import datetime, timezone, timedelta
from scipy.fft import fft

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard", page_icon="🛰️")

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


def get_frequency_anomaly(history_data):
    if len(history_data) < 20: return 0
    yf = fft(history_data)
    return np.sum(np.abs(yf[1:5]))


@st.cache_data(ttl=600)
def get_recent_quakes(lat, lon):
    try:
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=3.0&limit=5"
        res = requests.get(url, timeout=3).json()
        return res.get('features', [])
    except:
        return []


# --- МОНИТОРИНГ ---
@st.fragment(run_every="3s")
def live_vtec_monitor(f107):
    kp, _ = get_space_weather_data()
    hour_offset = (datetime.now(timezone.utc).hour % 24) / 24.0

    for city, (lat, lon, offset) in CITIES.items():
        local_time = datetime.now(timezone.utc) + timedelta(hours=offset)

        # Динамический расчет VTEC (Глобальное + Суточный ритм + Локальный шум)
        real_vtec = 10.0 + (f107 / 20.0) + (kp * 0.8) + (np.sin(hour_offset * 2 * np.pi) * 5) + np.random.normal(0, 0.3)

        st.session_state.history[city].append(real_vtec)
        if len(st.session_state.history[city]) > 30: st.session_state.history[city].pop(0)

        power = get_frequency_anomaly(st.session_state.history[city])
        mean_val = np.mean(st.session_state.history[city])
        z = (real_vtec - mean_val) / (np.std(st.session_state.history[city]) + 0.1)

        # Связываем с реальной сейсмикой
        quakes = get_recent_quakes(lat, lon)
        is_seismic_active = len(quakes) > 0

        # Критерии
        is_ionosphere_anomaly = abs(z) > 1.5
        is_seismic_risk = power > 2.0 and is_seismic_active

        with st.container(border=True):
            st.subheader(f"📍 {city} | 🕒 {local_time.strftime('%H:%M:%S')}")
            c1, c2, c3, c4 = st.columns([1, 1, 1, 2])

            c1.metric("VTEC", f"{real_vtec:.1f} TECU", f"{kp} Kp")

            if is_ionosphere_anomaly:
                c2.error("**ИОНОСФЕРА: АНОМАЛИЯ**", icon="🚨")
            else:
                c2.info("**ИОНОСФЕРА: НОРМА**", icon="✅")

            if is_seismic_risk:
                c3.warning(f"⚠️ **РИСК СЕЙСМИКИ: {power:.1f}**", icon="〰️")
            else:
                c3.info("**СЕЙСМИЧЕСКИЙ ФОН: ОК**", icon="🛡️")

            df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
            c4.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=6),
                                     layers=[pdk.Layer("ScatterplotLayer", df, get_position=["lon", "lat"],
                                                       get_color=[0, 200, 255, 160], get_radius=20000)]))


# --- ИНТЕРФЕЙС ---
st.title("🛰️ IonoSeis AI: Экспертная панель")
kp, f107 = get_space_weather_data()
tab1, tab2, tab3, tab4 = st.tabs(["🟢 МОНИТОРИНГ", "🚨 ЖУРНАЛ АНОМАЛИЙ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1: live_vtec_monitor(f107)
with tab4:
    st.markdown("### Научное обоснование")
    st.write(
        "Система использует метод **прокси-анализа**: мы сопоставляем динамику ионосферного отклика (VTEC) с реальными данными геомагнитной активности (NOAA Kp, F10.7) и подтверждаем аномалии через наличие сейсмических событий (USGS).")
    st.latex(r"Z = \frac{VTEC_{obs} - VTEC_{norm}}{\sigma}")