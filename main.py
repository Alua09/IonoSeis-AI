import streamlit as st
import pandas as pd
import requests
import json
import os

st.set_page_config(layout="wide", page_title="IonoSeis: Стабильный режим")
st.title("🛰 IonoSeis: Мониторинг сейсмики Алматы")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92
CACHE_FILE = "data_cache.json"


def get_seismic_data():
    try:
        # Стабильный источник USGS
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=200&minmagnitude=2"
        res = requests.get(url, timeout=10)

        if res.status_code == 200:
            data = res.json()
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f)
            return data
    except:
        pass

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return None


if st.button("🚀 ОБНОВИТЬ СЕЙСМИЧЕСКУЮ КАРТУ"):
    data = get_seismic_data()

    if data:
        features = data.get('features', [])
        records = []
        for f in features:
            props = f.get('properties', {})
            coords = f.get('geometry', {}).get('coordinates', [0, 0])
            records.append({
                'place': props.get('place', 'N/A'),
                'mag': props.get('mag', 0),
                'lat': coords[1],
                'lon': coords[0]
            })

        df = pd.DataFrame(records)
        # Расчет расстояния до Алматы
        df['dist'] = ((df['lat'] - ALMATY_LAT) ** 2 + (df['lon'] - ALMATY_LON) ** 2) ** 0.5 * 111

        # Только локальные события
        local = df[df['dist'] < 500].sort_values(by='dist')

        st.subheader("⚠️ Сейсмические события (Радиус 500 км от Алматы)")
        if not local.empty:
            st.dataframe(local[['place', 'mag', 'dist']], use_container_width=True)
        else:
            st.info("В радиусе 500 км событий не зафиксировано.")
    else:
        st.error("Серверы USGS сейчас недоступны. Проверьте соединение.")