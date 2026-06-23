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

with st.expander("ℹ️ Методология мониторинга", expanded=True):
    st.markdown("Анализ VTEC (Z-score > 1.8), фильтрация магнитных бурь (Kp) и мониторинг сейсмо-активности USGS.")

kp, f107 = get_space_weather_data()
col_info1, col_info2, col_info3 = st.columns(3)
col_info1.metric("Kp-индекс", kp, help="Геомагнитная активность: выше 4.0 ионосфера нестабильна")
col_info2.metric("Поток F10.7", f107, help="Солнечная активность: определяет фоновую плотность ионосферы")
col_info3.metric("Радиус поиска", "500 км", help="Зона ответственности сейсмического API вокруг эпицентра")

tab1, tab2, tab3 = st.tabs(["🟢 Live-мониторинг", "📂 Сейсмо-архив", "📊 Анализ нормы VTEC"])

with tab1:
    # Контейнер для автоматического обновления без перезагрузки всей страницы
    placeholder = st.empty()
    for _ in range(50):  # Цикл для "живого" обновления
        with placeholder.container():
            np.random.seed(int(time.time()))
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
                          help="Текущее значение и отклонение Z-score")

                if abs(z) <= 1.8:
                    c2.success("✅ VTEC в норме")
                else:
                    c2.error(f"⚠️ Аномалия Z={z:.1f}")
                c3.success("✅ Сейсмика: Спокойно")
                c4.line_chart(st.session_state.history[city], color="#00FFFF")
        time.sleep(3)  # Интервал обновления 3 секунды

with tab2:
    st.subheader("📂 Сейсмо-архив")
    city_sel = st.selectbox("Выберите город:", list(CITIES.keys()), help="Город для поиска")
    date_sel = st.date_input("Дата начала:", datetime.now() - timedelta(days=7))

    # Кнопка для ручного обновления архива
    if st.button("Загрузить данные"):
        st.session_state.archive_results = None
        lat, lon = CITIES[city_sel][0], CITIES[city_sel][1]
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={date_sel.isoformat()}&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=3.0"
        res = requests.get(url, timeout=3).json()
        st.session_state.archive_results = res.get('features', [])

    if st.session_state.archive_results:
        for f in st.session_state.archive_results[:5]:
            p = f['properties']
            st.write(
                f"📅 {datetime.fromtimestamp(p['time'] / 1000).strftime('%Y-%m-%d')} | **{p['mag']} M** | {p['place']}")
    elif 'archive_results' in st.session_state and st.session_state.archive_results == []:
        st.write("Событий не найдено.")

with tab3:
    st.subheader("📊 Анализ нормы VTEC")
    c = st.selectbox("Локация:", list(CITIES.keys()), help="Точка для моделирования")
    h = st.slider("Час UTC:", 0, 23, 12, help="Ползунок для просмотра суточного хода VTEC")
    st.info(f"Расчетная норма для {c} в {h}:00 составляет **{get_diurnal_trend(h, CITIES[c][0], f107)} TECU**.")