import streamlit as st
import pandas as pd
import requests
import json
import os

st.set_page_config(layout="wide", page_title="IonoSeis: Алматы Pro")
st.title("🛰 IonoSeis: Мониторинг сейсмики и ионосферы (Алматы)")

# Константы
ALMATY_LAT, ALMATY_LON = 43.25, 76.92
CACHE_FILE = "data_cache.json"


def get_data():
    try:
        # Сейсмика
        res_quake = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=200", timeout=5)
        # Солнечный поток (F10.7)
        res_solar = requests.get("https://services.swpc.noaa.gov/json/solar_cycle/observed_flux_values.json", timeout=5)

        data = {'quakes': res_quake.json(), 'solar': res_solar.json()}
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f)
        return data
    except:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    return None


if st.button("🚀 ОБНОВИТЬ ДАННЫЕ ДЛЯ АЛМАТЫ"):
    data = get_data()
    if data:
        # 1. Сейсмика: фильтр для Алматы (300 км)
        features = data['quakes'].get('features', [])
        records = [{'place': f['properties']['place'], 'mag': f['properties']['mag'],
                    'lat': f['geometry']['coordinates'][1], 'lon': f['geometry']['coordinates'][0]} for f in features]
        df = pd.DataFrame(records)
        df['dist'] = ((df['lat'] - ALMATY_LAT) ** 2 + (df['lon'] - ALMATY_LON) ** 2) ** 0.5 * 111
        local = df[df['dist'] < 300].sort_values(by='dist')

        st.subheader("⚠️ Сейсмические события (Радиус 300 км от Алматы)")
        if not local.empty:
            st.dataframe(local[['place', 'mag', 'dist']], use_container_width=True)
        else:
            st.info("В радиусе 300 км от Алматы событий не зафиксировано.")

        # 2. Ионосфера: Солнечный поток (F10.7)
        solar_df = pd.DataFrame(data['solar'][-20:])
        st.subheader("☀️ Индекс ионосферного воздействия (F10.7 Flux)")
        st.line_chart(solar_df.set_index('time-tag')['flux'])

    else:
        st.error("Ошибка загрузки данных.")