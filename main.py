import streamlit as st
import pandas as pd
import requests
import json
import os

st.set_page_config(layout="wide", page_title="IonoSeis: Финал")
st.title("🛰 IonoSeis: Сейсмо-ионосферная панель (Алматы)")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92
CACHE_FILE = "data_cache.json"


def get_full_data():
    try:
        # 1. Сейсмика (USGS)
        res_q = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100", timeout=8)
        # 2. Kp-индекс (стабильный JSON источник NOAA)
        res_k = requests.get("https://services.swpc.noaa.gov/products/noaa-k-index.json", timeout=8)

        if res_q.status_code == 200 and res_k.status_code == 200:
            data = {'quakes': res_q.json(), 'kp_data': res_k.json()}
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f)
            return data
    except:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    return None


if st.button("🚀 ОБНОВИТЬ СЕЙСМО-ИОНОСФЕРНЫЕ ДАННЫЕ"):
    data = get_full_data()
    if data:
        # --- Сейсмика Алматы ---
        features = data['quakes'].get('features', [])
        records = [{'place': f['properties']['place'], 'mag': f['properties']['mag'],
                    'lat': f['geometry']['coordinates'][1], 'lon': f['geometry']['coordinates'][0]} for f in features]
        df = pd.DataFrame(records)
        df['dist'] = ((df['lat'] - ALMATY_LAT) ** 2 + (df['lon'] - ALMATY_LON) ** 2) ** 0.5 * 111
        local = df[df['dist'] < 300].sort_values(by='dist')

        st.subheader("⚠️ Сейсмические события (Радиус 300 км от Алматы)")
        st.dataframe(local[['place', 'mag', 'dist']], use_container_width=True)

        # --- Ионосфера (Исправленный Kp-индекс) ---
        st.subheader("☀️ Состояние ионосферы (Kp-Index)")
        kp_df = pd.DataFrame(data['kp_data'], columns=['time', 'kp'])
        kp_df = kp_df.tail(20)  # Последние значения
        st.line_chart(kp_df.set_index('time')['kp'])
    else:
        st.error("Ошибка при получении данных. Попробуйте еще раз.")