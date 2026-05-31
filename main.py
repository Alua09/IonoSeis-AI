import streamlit as st
import pandas as pd
import requests
import json
import os

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis: Стабильный мониторинг")
st.title("🛰 IonoSeis: Сейсмо-ионосферная панель (Алматы)")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92
CACHE_FILE = "data_cache.json"


def get_stable_data():
    """Максимально защищенный сбор данных"""
    data = {"quakes": None, "kp": None}

    # Сбор сейсмики
    try:
        r_q = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100", timeout=10)
        if r_q.status_code == 200:
            data["quakes"] = r_q.json()
    except:
        pass

    # Сбор ионосферы (Kp-индекс)
    try:
        r_k = requests.get("https://kp.gfz-potsdam.de/app/files/Kp_ap_Ap_SN_F10.7_nowcast.json", timeout=10)
        if r_k.status_code == 200:
            data["kp"] = r_k.json()
    except:
        pass

    # Если что-то скачали, сохраняем в кэш
    if data["quakes"] or data["kp"]:
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f)
        return data

    # Если интернет упал совсем, берем из кэша
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None


# Интерфейс
if st.button("🚀 ЗАГРУЗИТЬ / ОБНОВИТЬ ДАННЫЕ"):
    data = get_stable_data()

    if data:
        # 1. Обработка сейсмики
        if data.get("quakes"):
            features = data["quakes"].get('features', [])
            records = [{'place': f['properties']['place'], 'mag': f['properties']['mag'],
                        'lat': f['geometry']['coordinates'][1], 'lon': f['geometry']['coordinates'][0]} for f in
                       features]
            df = pd.DataFrame(records)
            df['dist'] = ((df['lat'] - ALMATY_LAT) ** 2 + (df['lon'] - ALMATY_LON) ** 2) ** 0.5 * 111
            local = df[df['dist'] < 300].sort_values(by='dist')

            st.subheader("⚠️ Сейсмические события (Радиус 300 км от Алматы)")
            st.dataframe(local[['place', 'mag', 'dist']], use_container_width=True)
        else:
            st.warning("Сейсмические данные временно недоступны.")

        # 2. Обработка ионосферы
        if data.get("kp"):
            st.subheader("☀️ Состояние ионосферы (Kp-Index)")
            # Преобразуем данные GFZ (они часто приходят в виде словаря или списка списков)
            kp_data = data["kp"]
            if isinstance(kp_data, list):
                kp_df = pd.DataFrame(kp_data, columns=['date', 'kp'])
                st.line_chart(kp_df.tail(20).set_index('date')['kp'])
        else:
            st.warning("Данные ионосферы временно недоступны.")

    else:
        st.error("Нет подключения к сети и кэш пуст. Проверьте соединение.")