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

LOCATIONS = {
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
    tec_values = []
    with open("data.ionex", 'r', errors='ignore') as f:
        in_block = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_block = True
            elif 'END OF TEC MAP' in line:
                in_block = False
            elif in_block and not any(x in line for x in ['LAT/LON1/LON2', 'EPOCH', 'START', 'END']):
                for p in line.split():
                    try:
                        val = float(p)
                        if val < 9000: tec_values.append(val)
                    except:
                        continue
    return np.array(tec_values[:5183]).reshape((71, 73))


def get_tec_for_coords(grid, lat, lon):
    lat_idx = int((lat + 87.5) / 2.5)
    lon_idx = int((lon + 180) / 5.0)
    return grid[max(0, min(lat_idx, 70)), max(0, min(lon_idx, 72))]


def get_kp_index():
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
        data = requests.get(url, timeout=5).json()
        return float(data[-1][1])
    except:
        return "N/A"


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ЗАПУСТИТЬ ГЛОБАЛЬНЫЙ АНАЛИЗ"):
    with st.spinner("Синхронизация..."):
        try:
            setup_auth()
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now() - timedelta(days=2), datetime.now()),
                count=1
            )
            if results:
                files = earthaccess.download(results, "./tmp")
                grid = parse_upc_ionex(files[0])

                # Показываем Kp
                st.metric("Глобальный Kp-индекс", get_kp_index())

                # Показываем города
                cols = st.columns(3)
                for i, (city, (lat, lon)) in enumerate(LOCATIONS.items()):
                    tec = get_tec_for_coords(grid, lat, lon)
                    cols[i].metric(f"VTEC: {city}", f"{tec:.2f} TECU")

                # Карта
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(np.flipud(grid.T), cmap='inferno', extent=[-180, 180, -87.5, 87.5], aspect='auto')
                st.pyplot(fig)
            else:
                st.warning("Нет новых данных NASA.")
        except Exception as e:
            st.error(f"Ошибка: {e}")

st.write("Метод основан на японской концепции литосферно-ионосферного сопряжения.")