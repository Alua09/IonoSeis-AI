import streamlit as st
import pandas as pd
import requests
import json
import os

st.set_page_config(page_title="IonoSeis: Стабильный режим")
st.title("🛰 IonoSeis: Автономный мониторинг")

# Файл для хранения данных (локальный кэш)
CACHE_FILE = "data_cache.json"


def get_data():
    # 1. Сначала пробуем взять из интернета
    try:
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=10"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Сохраняем в файл, чтобы был "запас"
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f)
            return data
    except:
        pass

    # 2. Если интернет упал — берем из файла
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return None


if st.button("🚀 ПОКАЗАТЬ ДАННЫЕ"):
    data = get_data()
    if data:
        st.success("Данные успешно отображены (из сети или из кэша).")
        # Парсим и рисуем
        events = data.get('features', [])
        df = pd.DataFrame([f['properties'] for f in events])
        st.table(df[['place', 'mag', 'time']])
    else:
        st.error("Данные недоступны и кэш пуст. Пожалуйста, проверьте соединение.")