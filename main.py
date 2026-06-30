import streamlit as st
import json
import pandas as pd
import requests
import pydeck as pdk
import time
import os
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI", page_icon="🛰️")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'vtec_data.json')

CITIES = {
    "Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65), "Тайвань (Хуалянь)": (24.00, 121.60), "Стамбул": (41.00, 28.97)
}


# --- ФУНКЦИИ ---
@st.cache_data(ttl=300)
def get_seismic_data():
    """Получение землетрясений 4.5+ за последние 3 дня"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=3)
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time.strftime('%Y-%m-%d')}&minmagnitude=4.5"
    try:
        res = requests.get(url, timeout=5).json()
        features = res['features']
        data = []
        for f in features:
            props = f['properties']
            data.append({"Магнитуда": props['mag'], "Место": props['place'],
                         "Время": datetime.fromtimestamp(props['time'] / 1000).strftime('%d.%m %H:%M')})
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()


# --- ИНТЕРФЕЙС ---
data = load_vtec_data()  # (Ваша функция load_vtec_data)

st.title("🛰️ IonoSeis AI: Экспертный мониторинг")
tabs = st.tabs(["🟢 МОНИТОРИНГ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tabs[1]:
    st.subheader("Сейсмическая активность (4.5+ магнитуд за 3 дня)")
    df_quakes = get_seismic_data()
    if not df_quakes.empty:
        # Выделяем цветом магнитуду > 5.0
        def highlight_mag(row):
            return ['background-color: #ffcccc' if row['Магнитуда'] >= 5.0 else '' for _ in row]


        st.dataframe(df_quakes.style.apply(highlight_mag, axis=1), use_container_width=True)
    else:
        st.write("Нет значимых событий.")

with tabs[2]:
    st.markdown("""
    ### 🧪 Методология: VTEC и литосферно-ионосферные связи (LIS)
    Система базируется на концепции пресейсмической ионизации ионосферы.

    1. **Физический процесс:** Перед крупными землетрясениями в зоне разлома происходит накопление напряжений. Эманация радона, изменение геоэлектрических полей и выделение акустических волн приводят к **аномальному росту электронной плотности (VTEC)** в ионосфере над эпицентром.
    2. **Z-score (Статистическая аномалия):** Мы используем параметр *Z = (VTEC_current - VTEC_mean) / σ*. 
       - Значение **Z > 2.0** является статистически значимым сигналом о возмущении ионосферы (аномалия).
    3. **Интерпретация:** Аномалии, зафиксированные над активными сейсмическими разломами, рассматриваются как краткосрочные прекурсоры.

    *Система не является инструментом точного прогноза, а служит аналитической поддержкой для оценки геофизической обстановки.*
    """)