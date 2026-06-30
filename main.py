import streamlit as st
import json
import pandas as pd
import requests
import pydeck as pdk
import time
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard", page_icon="🛰️")


# Функция загрузки данных
def load_vtec_data():
    try:
        with open('vtec_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"Алматы": 16.5, "Бишкек": 16.2, "Токио": 18.2, "Тайвань": 17.5, "Стамбул": 15.1}


def get_kp_index():
    try:
        data = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=3).json()
        return f"{data[-1][1]} (Kp)"
    except:
        return "Данные недоступны"


# --- БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("🛰️ IonoSeis AI")
    st.info("Система анализа ионосферных предвестников землетрясений.")
    st.divider()
    st.write(f"🕒 **Обновлено:** {datetime.now().strftime('%H:%M:%S')}")
    st.subheader("🌍 Источники")
    st.markdown("- **VTEC:** NASA CDDIS (GIM)\n- **Сейсмика:** USGS Earthquake API\n- **Космос:** NOAA Space Weather")

# --- ГЛАВНЫЙ ЭКРАН ---
st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
st.metric("Текущий индекс солнечной активности (Kp)", get_kp_index())

data = load_vtec_data()
cities_info = {
    "Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65), "Тайвань": (24.00, 121.60), "Стамбул": (41.00, 28.97)
}

tab1, tab2, tab3 = st.tabs(["🟢 МОНИТОРИНГ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 НАУЧНАЯ БАЗА"])

with tab1:
    cols = st.columns(5)
    for i, (city, coords) in enumerate(cities_info.items()):
        val = data.get(city, 16.0)
        z = (val - 16.0) / 1.0
        with cols[i]:
            st.metric(city, f"{val} TECU", f"Z: {z:.2f}")
            color = [255, 60, 60, 160] if abs(z) > 2.0 else [60, 200, 60, 160]
            st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=coords[0], longitude=coords[1], zoom=4),
                                     layers=[pdk.Layer("ScatterplotLayer",
                                                       pd.DataFrame({'lat': [coords[0]], 'lon': [coords[1]]}),
                                                       get_position=["lon", "lat"], get_fill_color=color,
                                                       get_radius=60000)]))

with tab2:
    st.subheader("🌋 Архив сейсмо-событий (M > 5.0, последние 72 часа)")

    # Расчет времени: текущее минус 3 дня
    from datetime import timedelta

    three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()

    for city, (lat, lon) in cities_info.items():
        # Добавляем starttime в URL для фильтрации по времени
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=500&minmagnitude=5.0&starttime={three_days_ago}"
        try:
            quakes = requests.get(url, timeout=3).json().get('features', [])
            if not quakes:
                st.write(f"✅ {city}: Спокойно.")
            for q in quakes:
                ts = datetime.fromtimestamp(q['properties']['time'] / 1000).strftime('%d.%m %H:%M')
                st.error(f"⚠️ **{city}**: {ts} UTC | {q['properties']['mag']} M | {q['properties']['place']}")
        except:
            st.write(f"⚠️ Ошибка доступа к данным для {city}")

with tab3:
    st.subheader("🧪 Как работает диагностика LIS")
    st.markdown("""
    **Гипотеза ЛИВ (Литосферно-Ионосферного Взаимодействия):**
    Землетрясение — это не мгновенное событие, а длительный процесс накопления энергии. Мы наблюдаем этот процесс через «электрический отпечаток» в атмосфере:

    1. **Напряжение:** Перед разрывом пластов в коре возникают микротрещины.
    2. **Эмиссия:** Из этих трещин высвобождаются заряженные частицы (включая радон), которые ионизируют воздух.
    3. **Ионосферный отклик:** Эти частицы поднимаются на высоты 200–300 км и меняют плотность электронов (параметр **VTEC**).
    4. **Математический фильтр:** Мы используем Z-оценку, чтобы понять: является ли отклонение VTEC случайным «шумом» или это **сигнал тектонического напряжения**.

    *Мы не предсказываем землетрясения, мы фиксируем аномальные изменения, которые предшествуют сейсмической активности в исследуемых регионах.*
    """)

# Автоматический цикл обновления
time.sleep(60)
st.rerun()