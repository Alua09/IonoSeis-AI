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

CITIES = {
    "Алматы": (43.25, 76.92),
    "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65)
}


# --- ФУНКЦИИ ---
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
if st.button("🚀 ОБНОВИТЬ ВСЕ РЕГИОНЫ"):
    try:
        with st.spinner("Синхронизация..."):
            setup_auth()
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=5), datetime.now()), count=1)

            if results:
                files = earthaccess.download(results, "./tmp")
                grid = parse_upc_ionex(files[0])

                # Загружаем все землетрясения один раз
                quakes = requests.get(
                    "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100").json()

                st.subheader("Плотность ионосферы и Сейсмика по регионам")

                for city, (c_lat, c_lon) in CITIES.items():
                    st.markdown("---")
                    st.subheader(f"📍 Мониторинг: {city}")

                    # 1. VTEC
                    lat_idx, lon_idx = int((c_lat + 87.5) / 2.5), int((c_lon + 180) / 5)
                    val = grid[max(0, min(lat_idx, 70)), max(0, min(lon_idx, 72))]

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.metric(f"VTEC", f"{val:.2f} TECU")
                        fig, ax = plt.subplots(figsize=(6, 1))
                        ax.barh(0, val, color='skyblue' if val < 80 else 'red')
                        ax.set_xlim(0, 150)
                        st.pyplot(fig)

                    # 2. Сейсмика для этого города
                    with c2:
                        local_q = []
                        for f in quakes['features']:
                            lon, lat = f['geometry']['coordinates'][:2]
                            dist = ((lat - c_lat) ** 2 + (lon - c_lon) ** 2) ** 0.5 * 111
                            if dist < 1500 and f['properties']['mag'] > 3.0:
                                local_q.append({'place': f['properties']['place'], 'mag': f['properties']['mag']})

                        if local_q:
                            st.bar_chart(pd.DataFrame(local_q).set_index('place')['mag'])
                        else:
                            st.info(f"Спокойно: в радиусе 1500 км от {city} событий > 3.0 нет.")
            else:
                st.warning("Нет новых данных NASA.")
    except Exception as e:
        st.error(f"Ошибка: {e}")