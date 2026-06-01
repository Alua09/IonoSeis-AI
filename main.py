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

# --- НАСТРОЙКИ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
st.title("🛰 IonoSeis AI: Мониторинг ионосферы и сейсмики")

LOCATIONS = {"Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59), "Токио": (35.68, 139.65)}


# --- ФУНКЦИИ ---
def parse_upc_ionex(file_path):
    if not os.path.exists(file_path): return None
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
            elif in_block and not any(x in line for x in ['LAT/LON1/LON2', 'EPOCH', 'START', 'END']):
                for p in line.split():
                    try:
                        val = float(p)
                        if val < 9000: tec.append(val)
                    except:
                        continue
    return np.array(tec[:5183]).reshape((71, 73))


def get_kp_index():
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
        return float(requests.get(url, timeout=5).json()[-1][1])
    except:
        return "N/A"


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    with st.spinner("Синхронизация..."):
        try:
            # Пытаемся найти данные NASA
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now() - timedelta(days=5), datetime.now()),
                count=1
            )

            if results:
                files = earthaccess.download(results, "./tmp")
                grid = parse_upc_ionex(files[0])
            elif os.path.exists("backup_ionex.gz"):
                st.info("Данные NASA недоступны. Используем архивный файл.")
                grid = parse_upc_ionex("backup_ionex.gz")
            else:
                st.error("Данные не найдены и архив отсутствует. Загрузите backup_ionex.gz в проект.")
                grid = None

            if grid is not None:
                st.metric("Глобальный Kp-индекс", get_kp_index())
                cols = st.columns(3)
                for i, (city, (lat, lon)) in enumerate(LOCATIONS.items()):
                    lat_idx = int((lat + 87.5) / 2.5)
                    lon_idx = int((lon + 180) / 5.0)
                    tec = grid[max(0, min(lat_idx, 70)), max(0, min(lon_idx, 72))]
                    cols[i].metric(f"VTEC: {city}", f"{tec:.2f} TECU")

                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(np.flipud(grid.T), cmap='inferno', extent=[-180, 180, -87.5, 87.5], aspect='auto')
                st.pyplot(fig)
        except Exception as e:
            st.error(f"Критическая ошибка: {e}")

st.write("Метод мониторинга основан на литосферно-ионосферном сопряжении (LIC).")