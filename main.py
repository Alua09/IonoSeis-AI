import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis Pro: Алматы")
st.title("🛰 IonoSeis: Сейсмо-монитор (Центральная Азия)")

CACHE_FILE = "data_cache.json"


# Функция получения данных
def get_seismic_data():
    try:
        # USGS API для мировых данных
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100&minmagnitude=2"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f)
            return data
    except:
        pass

    # Резерв из кэша
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return None


# Основная логика
if st.button("🚀 ЗАГРУЗИТЬ / ОБНОВИТЬ ДАННЫЕ"):
    data = get_seismic_data()

    if data:
        # Парсинг GeoJSON
        features = data.get('features', [])
        records = []
        for f in features:
            props = f['properties']
            coords = f['geometry']['coordinates']
            records.append({
                'place': props['place'],
                'mag': props['mag'],
                'time': pd.to_datetime(props['time'], unit='ms'),
                'lat': coords[1],
                'lon': coords[0]
            })

        df = pd.DataFrame(records)

        # Локальный фильтр для Алматы (радиус ~500 км)
        # Координаты Алматы: 43.25, 76.92
        almaty_lat, almaty_lon = 43.25, 76.92
        df['dist'] = ((df['lat'] - almaty_lat) ** 2 + (df['lon'] - almaty_lon) ** 2) ** 0.5 * 111

        # Разделение данных
        local_quakes = df[df['dist'] < 800].sort_values(by='mag', ascending=False)

        st.subheader("⚠️ События в регионе (Центральная Азия)")
        if not local_quakes.empty:
            st.dataframe(local_quakes[['place', 'mag', 'time', 'dist']], use_container_width=True)
        else:
            st.info("В радиусе 800 км от Алматы событий не зафиксировано.")

        st.subheader("🌍 Глобальная статистика (Последние данные)")
        st.metric("Всего событий в кэше", len(df))
        st.metric("Max магнитуда в выборке", df['mag'].max())

        # Визуализация
        st.line_chart(df.set_index('time')['mag'])

    else:
        st.error("Ошибка сети: серверы недоступны и кэш пуст.")

st.sidebar.info("Монитор работает в автономном режиме с использованием локального кэша.")