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
st.title("🛰 IonoSeis AI: Глобальный мониторинг")

CITIES = {"Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59), "Токио": (35.68, 139.65)}

if 'prev_tec' not in st.session_state:
    st.session_state.prev_tec = {city: 0.0 for city in CITIES}


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
            elif in_block and not any(x in line for x in ['LAT/LON', 'EPOCH', 'START', 'END']):
                for p in line.split():
                    try:
                        val = float(p); tec.append(val if val < 9000 else 0)
                    except:
                        continue
    return np.array(tec[:5183]).reshape((71, 73))


def get_normalized_tec(grid, lat, lon):
    lat_idx = max(0, min(int((lat + 87.5) / 2.5), 70))
    lon_idx = max(0, min(int((lon + 180) / 5.0), 72))
    raw_val = grid[lat_idx, lon_idx]
    return raw_val / 10.0 if raw_val > 100 else raw_val


if st.button("🚀 ОБНОВИТЬ ДАННЫЕ ИОНОСФЕРЫ"):
    try:
        with st.spinner("Получение свежих карт IGS..."):
            setup_auth()
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=5), datetime.now()))

            if results:
                # Очистка и выбор самого свежего файла
                if os.path.exists("./tmp"): shutil.rmtree("./tmp")
                os.makedirs("./tmp")
                results.sort(key=lambda x: x['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime'],
                             reverse=True)

                files = earthaccess.download(results[0:1], "./tmp")
                grid = parse_upc_ionex(files[0])

                # Свежая сейсмика за 24ч
                start_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
                quakes = requests.get(
                    f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time}").json()

                for city, (c_lat, c_lon) in CITIES.items():
                    st.markdown("---")
                    st.subheader(f"📍 Регион: {city}")
                    val = get_normalized_tec(grid, c_lat, c_lon)

                    # Логика дельты
                    delta = val - st.session_state.prev_tec[city]
                    st.session_state.prev_tec[city] = val

                    st.metric("VTEC (TECU)", f"{val:.2f}", delta=f"{delta:.2f}" if abs(delta) > 0.05 else None)

                    # График
                    fig, ax = plt.subplots(figsize=(6, 1))
                    ax.barh(0, val, color='red' if val > 50 else 'skyblue')
                    ax.set_xlim(0, 100)
                    ax.set_yticks([])
                    st.pyplot(fig)
            else:
                st.warning("Серверы IGS не вернули новых карт.")
    except Exception as e:
        st.error(f"Ошибка: {e}")