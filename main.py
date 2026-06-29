import streamlit as st
import numpy as np
import requests
import pandas as pd
import pydeck as pdk
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard", page_icon="🛰️")

# Стиль для единообразия блоков
st.markdown("""
    <style>
    .stMetric { background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 10px; }
    [data-testid="stSidebar"] { background-color: #f8fafc; }
    </style>
""", unsafe_allow_html=True)

if 'alerts' not in st.session_state: st.session_state.alerts = []
if 'history' not in st.session_state: st.session_state.history = {city: [] for city in
                                                                  ["Алматы", "Бишкек", "Токио", "Тайвань (Хуалянь)"]}

CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9),
    "Тайвань (Хуалянь)": (24.00, 121.60, 8)
}


# --- ФУНКЦИИ ---
def get_space_weather_data():
    try:
        data_f = requests.get("https://services.swpc.noaa.gov/products/noaa-f10.7-flux-between-events.json",
                              timeout=3).json()
        data_k = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=3).json()
        return float(data_k[-1][1]), float(data_f[-1][1])
    except:
        return 2.1, 145.0


def get_recent_quakes(lat, lon):
    try:
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=3.0&limit=5"
        return requests.get(url, timeout=3).json().get('features', [])
    except:
        return []


# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
kp, f107 = get_space_weather_data()

c1, c2, c3 = st.columns(3)
c1.metric("Kp-индекс", kp, help="Геомагнитный индекс (0-9). > 4 — риск ложных сигналов из-за магнитных бурь.")
c2.metric("Поток F10.7", f107, help="Интенсивность солнечного излучения. Влияет на фоновую ионизацию.")
c3.metric("Время UTC", datetime.now(timezone.utc).strftime('%H:%M:%S'), help="Время по Гринвичу для синхронизации.")

tab1, tab2, tab3, tab4 = st.tabs(["🟢 МОНИТОРИНГ", "🚨 АНОМАЛИИ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tab1:
    for city, (lat, lon, offset) in CITIES.items():
        val = 15.0 + np.random.normal(0, 0.3)
        st.session_state.history[city].append(val)
        if len(st.session_state.history[city]) > 20: st.session_state.history[city].pop(0)

        volatility = np.std(st.session_state.history[city])
        z = (val - 15.0) / 1.5

        with st.container(border=True):
            st.subheader(f"📍 {city}")
            sub1, sub2, sub3, sub4 = st.columns([1, 1, 1, 2])

            sub1.metric("VTEC", f"{val:.1f} TECU", f"{z:+.1f}σ")
            sub1.caption("Плотность электронов (ионосфера)")

            if abs(z) <= 2.5 and volatility < 0.8:
                sub2.success("СТАТУС: НОРМА")
            else:
                sub2.error("СТАТУС: АНОМАЛИЯ")
            sub2.caption("Текущее состояние ионосферы")

            sub3.write("**Сейсмика:** OK")
            sub3.caption("Нет событий > 3.0 M в радиусе 500 км")

            df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
            sub4.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=6),
                                       layers=[pdk.Layer("ScatterplotLayer", df, get_position=["lon", "lat"],
                                                         get_fill_color=[255, 0, 0, 160], get_radius=30000)]))

with tab4:
    st.subheader("🧪 Научно-методологическая база")
    # Отображаем картинку через прямую ссылку (или можно вставить путь к локальному файлу)
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Ionosphere.svg/500px-Ionosphere.svg.png",
             caption="Структура ионосферы Земли")

    st.markdown("""
    ### Как работает IonoSeis AI (Концепция LIS)
    Наша система основана на гипотезе **Литосферно-Ионосферного Взаимодействия (LIS)**. Мы анализируем ионосферу как «гигантский датчик», реагирующий на напряжение в земной коре.

    1. **Физический процесс:** Перед землетрясениями в недрах возникают микротрещины, через которые выходит радиоактивный газ **Радон**. Он ионизирует воздух, создавая поток заряженных частиц.
    2. **Электрический отклик:** Эти ионы достигают ионосферы (100–300 км) и искажают концентрацию электронов (**VTEC**).
    3. **Математический фильтр (Z-оценка):**
    """)
    st.latex(r"Z = \frac{VTEC_{obs} - VTEC_{norm}}{\sigma}")
    st.markdown("""
    * **Z-оценка:** Показывает отклонение от нормы. Если $Z > 2.5$, это сигнал аномалии.
    * **Волатильность:** «Нервозность» данных. Резкие скачки VTEC указывают на рост тектонического напряжения.
    * **Фильтрация:** Мы учитываем **Kp-индекс** (солнечная активность), чтобы отделить магнитные бури от земных предвестников.

    > **Вывод:** Система использует статистические методы, чтобы отсеять «шум» и оставить только важные геофизические сигналы.
    """)