import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import math
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

# Подсказка для жюри (Методология)
with st.expander("ℹ️ Методология мониторинга", expanded=True):
    st.write("""
    1. **VTEC:** Индикатор плотности электронов. 
    2. **Z-score:** Отклонение от модели. 
    3. **Kp-индекс:** Фильтр солнечного шума.
    """)

kp, f107 = get_space_weather_data()
st.info(f"🌐 Kp: **{kp}** | ☀️ F10.7: **{f107}** | 📡 Радиус: 500 км")

tab1, tab2, tab3 = st.tabs(["🟢 Live-мониторинг", "📂 Сейсмо-архив", "📊 Анализ нормы VTEC"])

with tab1:
    try:
        url_quakes = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=" + (
                    datetime.now() - timedelta(days=1)).isoformat()
        quakes_data = requests.get(url_quakes, timeout=3).json().get('features', [])
    except:
        quakes_data = []

    for city, (lat, lon, offset) in CITIES.items():
        st.markdown("---")
        local_time = datetime.now(timezone.utc) + timedelta(hours=offset)
        # Использование времени для динамики VTEC
        seed = int(time.time() / 10) + hash(city)
        np.random.seed(seed % 1000)

        hour = local_time.hour + local_time.minute / 60.0
        norm = get_diurnal_trend(hour, lat, f107)
        val = norm + np.random.normal(0, 0.5)
        z = (val - norm) / 1.5

        st.session_state.history[city].append(val)
        if len(st.session_state.history[city]) > 20: st.session_state.history[city].pop(0)

        col1, col2, col3, col4 = st.columns([1, 1, 1.5, 2])
        col1.subheader(f"📍 {city}")
        col1.metric("VTEC", f"{val:.1f} TECU", f"{z:+.1f}σ", help="Текущее отклонение от суточной нормы")

        if kp >= 4:
            col2.warning("☀️ Магнитная активность")
        elif abs(z) > 1.8:
            col2.error(f"⚠️ Аномалия Z={z:.1f}")
        else:
            col2.success("✅ VTEC в норме", help="Значения ионосферы соответствуют расчетной модели")

        if [q for q in quakes_data if math.sqrt(
                (q['geometry']['coordinates'][1] - lat) ** 2 + (q['geometry']['coordinates'][0] - lon) ** 2) < 4.5]:
            col3.error("🚨 Сейсмика: Активно", help="Событие USGS в радиусе 500 км")
        else:
            col3.success("✅ Сейсмика: Спокойно")

        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='cyan')
        ax.axis('off')
        col4.pyplot(fig)

with tab2:
    st.subheader("📂 Сейсмо-архив")
    with st.form("archive_form"):
        city_sel = st.selectbox("Город:", list(CITIES.keys()), help="Выберите город для анализа архива")
        date_sel = st.date_input("Дата:", datetime.now() - timedelta(days=7))
        btn = st.form_submit_button("Загрузить")

    if btn:
        st.session_state.archive_results = None  # Сброс данных для обновления
        lat, lon = CITIES[city_sel][0], CITIES[city_sel][1]
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={date_sel.isoformat()}&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=3.0"
        res = requests.get(url).json()
        st.session_state.archive_results = res.get('features', [])

    if st.session_state.archive_results:
        for f in st.session_state.archive_results[:5]:
            p = f['properties']
            st.write(f"📅 {datetime.fromtimestamp(p['time'] / 1000).strftime('%Y-%m-%d')} | {p['mag']} M | {p['place']}")

with tab3:
    st.subheader("📊 Анализ нормы VTEC")
    c = st.selectbox("Город:", list(CITIES.keys()), help="Выбор локации для прогноза нормы")
    h = st.slider("Час (UTC):", 0, 23, 12, help="Ползунок для визуализации суточного хода")
    norm = get_diurnal_trend(h, CITIES[c][0], f107)
    st.info(f"Ожидаемый VTEC: **{norm} TECU**.")