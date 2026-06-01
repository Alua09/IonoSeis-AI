import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import requests
import gzip
import shutil
import os
import pandas as pd
from datetime import datetime, timedelta

# Настройка
st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
st.title("🛰 IonoSeis AI: Мониторинг ионосферы и сейсмики")

# Координаты для мониторинга
CITIES = {
    "Алматы": (43.25, 76.92),
    "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65)
}


def setup_auth():
    os.environ['EARTHDATA_USERNAME'] = st.secrets['EARTHDATA_USERNAME']
    os.environ['EARTHDATA_PASSWORD'] = st.secrets['EARTHDATA_PASSWORD']
    return earthaccess.login(strategy="environment")


def parse_upc_ionex(file_path):
    with gzip.open(file_path, 'rb') as f_in:
        with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
    tec = []
    with open("data.ionex", 'r', errors='ignore') as f:
        in_block = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_block = True
            elif 'END OF TEC MAP' in line:
                in_block = False
            elif in_block and not any(x in line for x in ['LAT/LON', 'EPOCH']):
                for p in line.split():
                    try:
                        val = float(p); tec.append(val if val < 9000 else 0)
                    except:
                        continue
    return np.array(tec[:5183]).reshape((71, 73))


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    try:
        with st.spinner("Синхронизация с серверами..."):
            setup_auth()
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=5), datetime.now()), count=1)

            if results:
                files = earthaccess.download(results, "./tmp")
                grid = parse_upc_ionex(files[0])

                # 1. СЕКЦИЯ: VTEC по городам (Тот самый ваш график)
                st.subheader("Плотность ионосферы (VTEC) в регионах")
                cols = st.columns(3)
                for i, (city, (lat, lon)) in enumerate(CITIES.items()):
                    lat_idx, lon_idx = int((lat + 87.5) / 2.5), int((lon + 180) / 5)
                    val = grid[max(0, min(lat_idx, 70)), max(0, min(lon_idx, 72))]

                    with cols[i]:
                        st.metric(f"VTEC: {city}", f"{val:.2f} TECU")
                        fig, ax = plt.subplots(figsize=(8, 1.5))
                        ax.barh(0, val, color='skyblue' if val < 80 else 'red')
                        ax.set_xlim(0, 150)
                        ax.set_title(f"Уровень {city}")
                        st.pyplot(fig)

                # 2. СЕКЦИЯ: Сейсмика USGS
                st.subheader("Сейсмическая активность (USGS)")
                quakes = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=50").json()
                local_quakes = []
                for f in quakes['features']:
                    lon, lat = f['geometry']['coordinates'][:2]
                    dist = ((lat - 43.25) ** 2 + (lon - 76.92) ** 2) ** 0.5 * 111
                    if dist < 1500 and f['properties']['mag'] > 3.0:
                        local_quakes.append({'place': f['properties']['place'], 'mag': f['properties']['mag']})

                if local_quakes:
                    st.bar_chart(pd.DataFrame(local_quakes).set_index('place')['mag'])
                else:
                    st.info("Спокойно: в радиусе 1500 км событий > 3.0 нет.")
            else:
                st.warning("Нет новых данных NASA.")
    except Exception as e:
        st.error(f"Ошибка: {e}")