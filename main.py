import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime

st.set_page_config(layout="wide", page_title="IonoSeis: Аналитика")
st.title("🛰 IonoSeis: Мониторинг сейсмики")

CACHE_FILE = "data_cache.json"


def get_data():
    try:
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=20"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f)
            return data
    except:
        pass
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return None


if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    data = get_data()
    if data:
        # Парсинг и приведение к удобному виду
        events = data.get('features', [])
        df = pd.DataFrame([f['properties'] for f in events])

        # Конвертация времени: миллисекунды -> читаемая дата
        df['time'] = pd.to_datetime(df['time'], unit='ms')

        # Сортировка по времени (новые сверху)
        df = df.sort_values(by='time', ascending=False)

        # Вывод таблицы с нужными колонками
        st.dataframe(df[['place', 'mag', 'time']], use_container_width=True)

        # Краткая аналитика
        st.metric("Всего событий в выборке", len(df))
        st.metric("Максимальная магнитуда", df['mag'].max())
    else:
        st.error("Данные недоступны.")