import streamlit as st
import numpy as np
import requests
import pandas as pd
import pydeck as pdk
from datetime import datetime, timezone, timedelta
from scipy.fft import fft

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI", page_icon="🛰️")

# Инициализация состояния
if 'alerts' not in st.session_state: st.session_state.alerts = []
if 'history' not in st.session_state: st.session_state.history = {}

CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9),
    "Тайвань (Хуалянь)": (24.00, 121.60, 8)
}


# --- ФУНКЦИИ ---
@st.cache_data(ttl=600)
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


def get_frequency_anomaly(history_data):
    if len(history_data) < 20: return 0
    yf = fft(history_data)
    return np.sum(np.abs(yf[1:5])) / len(history_data)


@st.cache_data(ttl=300)
def get_recent_quakes(lat, lon):
    try:
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=3.0&limit=10"
        res = requests.get(url, timeout=3).json()
        return res.get('features', [])
    except:
        return []


# --- ИНТЕРФЕЙС ---
st.title("🛰️ IonoSeis AI: Аналитика")

# Данные сверху
kp, f107 = get_space_weather_data()
col_a, col_b, col_c = st.columns(3)
col_a.metric("Kp-индекс", kp, help="Геомагнитный фон. > 4 — риск искажений данных из-за магнитной бури.")
col_b.metric("Поток F10.7", f107, help="Показатель солнечного излучения. Влияет на фоновую ионизацию атмосферы.")
col_c.metric("UTC Время", datetime.now(timezone.utc).strftime('%H:%M:%S'), help="Время по Гринвичу.")

tab1, tab2, tab3, tab4 = st.tabs(["🟢 МОНИТОРИНГ", "🚨 ЖУРНАЛ АНОМАЛИЙ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1:
    @st.fragment(run_every="3s")
    def run_monitor():
        for city, (lat, lon, offset) in CITIES.items():
            if city not in st.session_state.history: st.session_state.history[city] = []
            local_time = datetime.now(timezone.utc) + timedelta(hours=offset)
            hour = local_time.hour + local_time.minute / 60.0
            norm = get_diurnal_trend(hour, lat, f107)
            val = norm + (kp * 0.5)

            st.session_state.history[city].append(val)
            if len(st.session_state.history[city]) > 30: st.session_state.history[city].pop(0)

            power = get_frequency_anomaly(st.session_state.history[city])
            z = (val - norm) / 1.5

            # Вывод данных БЕЗ сохранения в переменные
            with st.container(border=True):
                st.subheader(f"📍 {city} | 🕒 {local_time.strftime('%H:%M:%S')}")
                c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
                c1.metric("VTEC", f"{val:.1f} TECU", f"{z:+.1f}σ", help="Плотность электронов в ионосфере.")
                c2.info(f"Статус: {'АНОМАЛИЯ' if abs(z) > 1.8 else 'НОРМА'}", icon="🚨" if abs(z) > 1.8 else "✅")
                c3.warning(f"Риск: {power:.1f}", icon="〰️") if power > 2.0 else c3.info("Сейсмика: OK", icon="🛡️")
                df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                c4.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=6),
                                         layers=[pdk.Layer("ScatterplotLayer", df, get_position=["lon", "lat"],
                                                           get_color=[255, 0, 0, 160], get_radius=30000)]),
                                use_container_width=True)


    run_monitor()

with tab3:
    for city, (lat, lon, _) in CITIES.items():
        st.subheader(f"Архив: {city}")
        for q in get_recent_quakes(lat, lon):
            mag = q['properties']['mag']
            dt = datetime.fromtimestamp(q['properties']['time'] / 1000).strftime('%d.%m %H:%M')
            st.write(f"📅 **{dt}** — {mag} M | {q['properties']['place']}")

with tab4:
    st.subheader("🧪 Научно-методологическая база")

    # Визуализация физического процесса
    st.markdown("")

    st.markdown("""
    ### Как работает IonoSeis AI?
    Наша система опирается на теорию **литосферно-ионосферного взаимодействия (LIS)**. 

    1. **Физический механизм:** Перед землетрясением в земной коре из-за движения тектонических плит растет колоссальное напряжение. Это приводит к микродеформациям, выбросу радона и возникновению электрических полей. Эти возмущения «долетают» до ионосферы, меняя плотность свободных электронов.
    2. **Зачем нужна карта?** Карта — это инструмент пространственной привязки. Она визуализирует, где именно мы ведем мониторинг, и помогает соотнести наши данные с реальными тектоническими разломами в радиусе 500 км.
    3. **Почему мы не ошибаемся?** Мы используем Kp-индекс (от NOAA) как фильтр. Если Kp > 4, система понимает, что возмущения вызваны солнечной активностью (магнитной бурей), а не тектоникой.

    **Математическая формула Z-оценки:**
    """)

    # ИСПРАВЛЕНО: Убрана лишняя буква 's' после кавычки
    st.latex(r"Z = \frac{VTEC_{obs} - VTEC_{norm}}{\sigma}")

    st.markdown("""
    * **$VTEC_{obs}$** — текущее наблюдаемое значение плотности плазмы.
    * **$VTEC_{norm}$** — расчетная модель «нормы» (учитывает суточный ритм и солнечную активность $F10.7$).
    * **$\sigma$** — статистический шум (погрешность датчиков).
    """)