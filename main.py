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


# 2. Ионосфера (с резервированием и кэшем)
def get_kp_index():
    urls = [
        "https://services.swpc.noaa.gov/products/noaa-k-index.json",
        "https://kp.gfz-potsdam.de/app/files/Kp_ap_Ap_SN_F10.7_nowcast.json"
    ]
    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                with open(KP_CACHE, 'w') as f:
                    json.dump(data, f)
                return pd.DataFrame(data[1:], columns=['time', 'kp'])
        except:
            continue

    if os.path.exists(KP_CACHE):
        with open(KP_CACHE, 'r') as f:
            data = json.load(f)
            return pd.DataFrame(data[1:], columns=['time', 'kp'])
    return None


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    seismic = get_seismic()
    kp_df = get_kp_index()

    col1, col2 = st.columns(2)

    # Сейсмо-блок
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

    # Ионосферный блок
    with col2:
        st.subheader("☀️ Ионосфера (Kp-Index)")
        if kp_df is not None and not kp_df.empty:
            kp_val = float(kp_df.iloc[-1]['kp'])
            status = "Стабильно" if kp_val < 4 else "АКТИВНОСТЬ"
            st.metric("Kp-индекс", kp_val, status)
            st.line_chart(kp_df.tail(15).set_index('time')['kp'])
        else:
            st.warning("Данные ионосферы пока не загружены. Нажмите кнопку.")

st.sidebar.markdown("---")
st.sidebar.write("Статус системы: **Активна**")