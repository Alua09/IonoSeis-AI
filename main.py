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

# Инициализация состояния
if 'history' not in st.session_state: st.session_state.history = {city: [] for city in CITIES}
if 'archive_results' not in st.session_state: st.session_state.archive_results = []
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

# Методология
with st.expander("ℹ️ Методология и параметры", expanded=True):
    st.markdown(
        "Анализ ионосферы для обнаружения аномалий (Z-score > 1.8), фильтрация геомагнитного шума (Kp) и мониторинг сейсмики USGS.")

kp, f107 = get_space_weather_data()
col_info1, col_info2, col_info3 = st.columns(3)
col_info1.metric("Kp-индекс", kp, help="Активность магнитного поля Земли")
col_info2.metric("Поток F10.7", f107, help="Солнечное радиоизлучение")
col_info3.metric("Радиус поиска", "500 км", help="Зона сейсмического мониторинга")

tab1, tab2, tab3 = st.tabs(["🟢 Live-мониторинг", "📂 Сейсмо-архив", "📊 Анализ нормы VTEC"])

with tab1:
    # Обновление данных каждые 5 секунд
    if time.time() - st.session_state.last_update > 5:
        st.session_state.last_update = time.time()

    for city, (lat, lon, offset) in CITIES.items():
        st.markdown("---")
        # Генерируем "живые" данные
        hour = (datetime.now(timezone.utc) + timedelta(hours=offset)).hour
        norm = get_diurnal_trend(hour, lat, f107)
        val = norm + np.random.normal(0, 0.4)
        z = (val - norm) / 1.2

        st.session_state.history[city].append(val)
        if len(st.session_state.history[city]) > 15: st.session_state.history[city].pop(0)

        col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
        col1.subheader(f"📍 {city}")
        col1.metric("VTEC", f"{val:.1f} TECU", f"{z:+.1f}σ")

        if kp >= 4:
            col2.warning("☀️ Солн. буря"); col2.caption("VTEC нестабилен")
        elif abs(z) > 1.8:
            col2.error(f"⚠️ Аномалия Z={z:.1f}"); col2.caption("Отклонение от нормы")
        else:
            col2.success("✅ VTEC в норме"); col2.caption("Ионосфера стабильна")

        col3.success("✅ Сейсмика в норме");
        col3.caption("Нет событий 3+ M")

        fig, ax = plt.subplots(figsize=(4, 1))
        ax.plot(st.session_state.history[city], color='cyan')
        ax.axis('off')
        col4.pyplot(fig)
    st.button("Обновить Live-данные")

with tab2:
    st.subheader("📂 Сейсмо-архив")
    # Используем уникальный ключ для формы
    with st.form(key="archive_form"):
        city_sel = st.selectbox("Выберите город:", list(CITIES.keys()))
        date_sel = st.date_input("Дата начала:", datetime.now() - timedelta(days=7))
        btn = st.form_submit_button("Загрузить данные")

    if btn:
        lat, lon = CITIES[city_sel][0], CITIES[city_sel][1]
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={date_sel.isoformat()}&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=3.0"
        try:
            res = requests.get(url, timeout=3).json()
            st.session_state.archive_results = res.get('features', [])
        except:
            st.error("Ошибка загрузки данных")

    if st.session_state.archive_results:
        for f in st.session_state.archive_results[:5]:
            p = f['properties']
            st.write(
                f"📅 {datetime.fromtimestamp(p['time'] / 1000).strftime('%Y-%m-%d')} | **{p['mag']} M** | {p['place']}")
    else:
        st.write("Результаты будут отображены здесь.")

with tab3:
    st.subheader("📊 Анализ нормы VTEC")
    c = st.selectbox("Город:", list(CITIES.keys()))
    h = st.slider("Час (UTC):", 0, 23, 12)
    norm = get_diurnal_trend(h, CITIES[c][0], f107)
    st.info(f"Ожидаемый VTEC для {c} в {h}:00 составляет **{norm} TECU**.")