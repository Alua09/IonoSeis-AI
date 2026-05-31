import streamlit as st
import pandas as pd
import requests
import json
import os

st.set_page_config(layout="wide", page_title="IonoSeis Pro: Финал")
st.title("🛰 IonoSeis: Сейсмо-ионосферная панель (Алматы)")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92
CACHE_FILE = "data_cache.json"


def get_full_data():
    try:
        # Сейсмика
        res_q = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100", timeout=8)
        # Геомагнитный индекс Kp (альтернативный надежный API)
        res_k = requests.get("https://services.swpc.noaa.gov/text/wing-kp-index.txt", timeout=8)

        data = {'quakes': res_q.json(), 'kp_raw': res_k.text}
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f)
        return data
    except:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    return None


if st.button("🚀 ОБНОВИТЬ СЕЙСМО-ИОНОСФЕРНЫЙ ДАННЫЕ"):
    data = get_full_data()
    if data:
        # --- Сейсмика ---
        features = data['quakes'].get('features', [])
        records = [{'place': f['properties']['place'], 'mag': f['properties']['mag'],
                    'lat': f['geometry']['coordinates'][1], 'lon': f['geometry']['coordinates'][0]} for f in features]
        df = pd.DataFrame(records)
        df['dist'] = ((df['lat'] - ALMATY_LAT) ** 2 + (df['lon'] - ALMATY_LON) ** 2) ** 0.5 * 111
        local = df[df['dist'] < 300].sort_values(by='dist')

        st.subheader("⚠️ Сейсмические события (Радиус 300 км от Алматы)")
        st.dataframe(local[['place', 'mag', 'dist']], use_container_width=True)

        # --- Ионосфера ---
        st.subheader("☀️ Состояние ионосферы (Kp-Index)")
        st.info("Kp-индекс выше 5 указывает на геомагнитную бурю, влияющую на ионосферу.")
        st.text(data['kp_raw'][-500:])  # Показываем последние данные из текстового потока
    else:
        st.error("Ошибка сети. Попробуйте обновить страницу.")

st.sidebar.markdown("---")
st.sidebar.write("Статус: **Система активна**")