import streamlit as st
import pandas as pd
import requests
import json
import os

# Настройка страницы
st.set_page_config(page_title="IonoSeis Pro", layout="wide")
st.title("🛰 IonoSeis: Мониторинг сейсмики и ионосферы")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92
KP_CACHE = "kp_cache.json"


# 1. Сейсмика
@st.cache_data(ttl=300)
def get_seismic():
    try:
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100"
        response = requests.get(url, timeout=10)
        return response.json() if response.status_code == 200 else None
    except:
        return None


# 2. Ионосфера (через прокси с fallback на кэш)
def get_kp_index():
    # Прокси для обхода блокировок
    url = "https://api.allorigins.win/get?url=https://services.swpc.noaa.gov/products/noaa-k-index.json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = json.loads(response.json()['contents'])
            df = pd.DataFrame(content[1:], columns=['time', 'kp'])
            df.to_json(KP_CACHE)  # Сохраняем в кэш
            return df
    except:
        pass

    # Если прокси не ответил, пытаемся прочитать файл кэша
    if os.path.exists(KP_CACHE):
        return pd.read_json(KP_CACHE)
    return None


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ОБНОВИТЬ СИСТЕМУ"):
    seismic = get_seismic()
    kp_df = get_kp_index()

    col1, col2 = st.columns(2)

    # Блок Сейсмики
    with col1:
        st.subheader("⚠️ Сейсмика (Алматы 300 км)")
        if seismic:
            features = seismic.get('features', [])
            records = [{'place': f['properties']['place'], 'mag': f['properties']['mag'],
                        'lat': f['geometry']['coordinates'][1], 'lon': f['geometry']['coordinates'][0]} for f in
                       features]
            df = pd.DataFrame(records)
            df['dist'] = ((df['lat'] - ALMATY_LAT) ** 2 + (df['lon'] - ALMATY_LON) ** 2) ** 0.5 * 111
            local = df[df['dist'] < 300].sort_values(by='dist')
            if not local.empty:
                st.dataframe(local[['place', 'mag', 'dist']], use_container_width=True)
            else:
                st.info("Тишина: в радиусе 300 км событий нет.")
        else:
            st.error("Сервер сейсмики недоступен.")

    # Блок Ионосферы
    with col2:
        st.subheader("☀️ Ионосфера (Kp-Index)")
        if kp_df is not None and not kp_df.empty:
            try:
                kp_val = float(kp_df.iloc[-1]['kp'])
                status = "Стабильно" if kp_val < 4 else "АКТИВНОСТЬ"
                st.metric("Kp-индекс", kp_val, status)
                st.line_chart(kp_df.tail(15).set_index('time')['kp'])
            except:
                st.warning("Ошибка обработки данных.")
        else:
            st.warning("Данные еще не были загружены. Попробуйте еще раз через минуту.")

st.sidebar.markdown("---")
st.sidebar.write("### Статус: Активен")