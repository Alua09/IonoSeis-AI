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

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
st.title("🛰 IonoSeis AI: Мониторинг ионосферы и сейсмики")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92


# --- ФУНКЦИИ ---
def setup_auth():
    os.environ['EARTHDATA_USERNAME'] = st.secrets['EARTHDATA_USERNAME']
    os.environ['EARTHDATA_PASSWORD'] = st.secrets['EARTHDATA_PASSWORD']
    return earthaccess.login(strategy="environment")


def parse_upc_ionex(file_path):
    with gzip.open(file_path, 'rb') as f_in:
        with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)

    tec_values = []
    with open("data.ionex", 'r', errors='ignore') as f:
        in_block = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_block = True
            elif 'END OF TEC MAP' in line:
                in_block = False
            elif in_block and not any(x in line for x in ['LAT/LON1/LON2', 'EPOCH', 'START', 'END']):
                parts = line.split()
                for p in parts:
                    try:
                        val = float(p)
                        if val < 9000: tec_values.append(val)
                    except:
                        continue
    return np.array(tec_values[:5183]).reshape((71, 73))


def get_almaty_tec(grid):
    lat_idx = int((ALMATY_LAT + 87.5) / 2.5)
    lon_idx = int((ALMATY_LON + 180) / 5.0)
    return grid[lat_idx, lon_idx]


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    try:
        with st.spinner("Синхронизация с серверами..."):
            setup_auth()
            # 1. Ионосфера
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now() - timedelta(days=5), datetime.now()),
                count=1
            )

            if results and len(results) > 0:
                files = earthaccess.download(results, "./tmp")
                grid = parse_upc_ionex(files[0])
                val = get_almaty_tec(grid)

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Плотность ионосферы над Алматы (VTEC)", f"{val:.2f} TECU")
                    fig, ax = plt.subplots(figsize=(10, 2))
                    ax.barh(0, val, color='skyblue' if val < 80 else 'red')
                    ax.set_xlim(0, 150)
                    ax.set_title("Текущий уровень VTEC (Норма до 80 TECU)")
                    st.pyplot(fig)

                # 2. Сейсмика
                quakes = requests.get(
                    "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100").json()
                local_quakes = []
                for f in quakes['features']:
                    lon, lat = f['geometry']['coordinates'][:2]
                    dist = ((lat - ALMATY_LAT) ** 2 + (lon - ALMATY_LON) ** 2) ** 0.5 * 111
                    if dist < 1000 and f['properties']['mag'] > 2.0:
                        local_quakes.append(
                            {'place': f['properties']['place'], 'mag': f['properties']['mag'], 'dist': round(dist)})

                with col2:
                    st.subheader("Сейсмика (Алматы 1000 км)")
                    if local_quakes:
                        df_q = pd.DataFrame(local_quakes)
                        st.bar_chart(df_q.set_index('place')['mag'])
                        for q in local_quakes:
                            st.write(f"🔹 {q['place']} | M: {q['mag']} | {q['dist']} км")
                    else:
                        st.info("Спокойно: в радиусе 1000 км событий > 2.0 нет.")
            else:
                st.warning("Нет новых данных NASA.")
    except Exception as e:
        st.error(f"Ошибка: {e}")