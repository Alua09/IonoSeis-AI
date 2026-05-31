import streamlit as st
import pandas as pd
import requests
import json
import os

st.set_page_config(layout="wide", page_title="IonoSeis: Статус системы")
st.title("🛰 IonoSeis: Диагностика мониторинга")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92
CACHE_FILE = "data_cache.json"


def get_data():
    try:
        # Увеличиваем таймаут для медленных ответов
        res_quake = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100",
                                 timeout=10)
        res_solar = requests.get("https://services.swpc.noaa.gov/json/solar_cycle/observed_flux_values.json",
                                 timeout=10)

        if res_quake.status_code == 200 and res_solar.status_code == 200:
            data = {'quakes': res_quake.json(), 'solar': res_solar.json()}
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f)
            return data
        else:
            return {"error": f"API Error: Quake {res_quake.status_code}, Solar {res_solar.status_code}"}
    except Exception as e:
        return {"error": str(e)}


if st.button("🚀 ПРОВЕРИТЬ СОЕДИНЕНИЕ И ОБНОВИТЬ"):
    with st.spinner("Запрос к сейсмостанциям..."):
        result = get_data()

        # Если есть ошибка, пробуем показать хоть что-то из кэша
        if "error" in result and os.path.exists(CACHE_FILE):
            st.warning(f"Прямой запрос не удался: {result['error']}. Используем последние сохраненные данные.")
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
        elif "error" in result:
            st.error(f"Критическая ошибка сети: {result['error']}. Пожалуйста, попробуйте позже.")
            data = None
        else:
            data = result

        if data:
            # Парсинг данных
            try:
                features = data['quakes'].get('features', [])
                records = []
                for f in features:
                    props = f.get('properties', {})
                    coords = f.get('geometry', {}).get('coordinates', [0, 0])
                    records.append({'place': props.get('place', 'N/A'), 'mag': props.get('mag', 0), 'lat': coords[1],
                                    'lon': coords[0]})

                df = pd.DataFrame(records)
                df['dist'] = ((df['lat'] - ALMATY_LAT) ** 2 + (df['lon'] - ALMATY_LON) ** 2) ** 0.5 * 111
                local = df[df['dist'] < 500].sort_values(by='dist')

                st.subheader("⚠️ Сейсмические события (Радиус 500 км)")
                st.dataframe(local)

                st.subheader("☀️ Солнечный поток")
                st.line_chart(pd.DataFrame(data['solar'][-20:]).set_index('time-tag')['flux'])
            except Exception as e:
                st.error(f"Ошибка при чтении данных: {e}")