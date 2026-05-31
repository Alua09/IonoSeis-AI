import streamlit as st
import pandas as pd
import requests
import json
import os

st.set_page_config(layout="wide", page_title="IonoSeis: Алматы Pro")
st.title("🛰 IonoSeis: Мониторинг Алматы")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92
CACHE_FILE = "data_cache.json"


def get_data():
    try:
        # Запрос сейсмики
        res_quake = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=200", timeout=5)
        # Запрос солнечного потока
        res_solar = requests.get("https://services.swpc.noaa.gov/json/solar_cycle/observed_flux_values.json", timeout=5)

        if res_quake.status_code == 200 and res_solar.status_code == 200:
            data = {'quakes': res_quake.json(), 'solar': res_solar.json()}
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f)
            return data
    except:
        pass

    # Если интернет упал или ошибка API, читаем кэш, если он есть
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                # Проверка: если файл поврежден или нет ключей, удаляем его
                if 'quakes' in data and 'solar' in data:
                    return data
                else:
                    os.remove(CACHE_FILE)
        except:
            os.remove(CACHE_FILE)
    return None


if st.button("🚀 ЗАГРУЗИТЬ / ОБНОВИТЬ"):
    data = get_data()
    if data and 'quakes' in data:
        # Сейсмика: фильтр для Алматы
        features = data['quakes'].get('features', [])
        records = []
        for f in features:
            props = f['properties']
            coords = f['geometry']['coordinates']
            records.append({
                'place': props.get('place', 'N/A'),
                'mag': props.get('mag', 0),
                'lat': coords[1],
                'lon': coords[0]
            })

        df = pd.DataFrame(records)
        df['dist'] = ((df['lat'] - ALMATY_LAT) ** 2 + (df['lon'] - ALMATY_LON) ** 2) ** 0.5 * 111
        local = df[df['dist'] < 300].sort_values(by='dist')

        st.subheader("⚠️ Сейсмические события (Радиус 300 км от Алматы)")
        if not local.empty:
            st.dataframe(local[['place', 'mag', 'dist']], use_container_width=True)
        else:
            st.info("В радиусе 300 км событий не зафиксировано.")

        # Солнечный поток
        if 'solar' in data:
            st.subheader("☀️ Индекс солнечного потока (F10.7)")
            solar_df = pd.DataFrame(data['solar'][-20:])
            st.line_chart(solar_df.set_index('time-tag')['flux'])
    else:
        st.error("Данные недоступны. Попробуйте обновить страницу.")