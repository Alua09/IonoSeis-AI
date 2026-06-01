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
st.title("🛰 IonoSeis AI: Глобальный мониторинг ионосферы и сейсмики")

# Словарь городов для мониторинга
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
                parts = line.split()
                for p in parts:
                    try:
                        val = float(p)
                        if val < 9000: tec_values.append(val)
                    except:
                        continue
    return np.array(tec_values[:5183]).reshape((71, 73))


# Универсальная функция для получения VTEC по координатам
def get_tec_for_coords(grid, lat, lon):
    lat_idx = int((lat + 87.5) / 2.5)
    lon_idx = int((lon + 180) / 5.0)
    # Ограничиваем индексы, чтобы не выйти за пределы массива
    lat_idx = max(0, min(lat_idx, 70))
    lon_idx = max(0, min(lon_idx, 72))
    return grid[lat_idx, lon_idx]


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    try:
        with st.spinner("Синхронизация с серверами..."):
            setup_auth()
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now() - timedelta(days=5), datetime.now()),
                count=1
            )

            if results and len(results) > 0:
                files = earthaccess.download(results, "./tmp")
                grid = parse_upc_ionex(files[0])

                # 1. Метрики по городам
                cols = st.columns(3)
                for i, (city, (lat, lon)) in enumerate(LOCATIONS.items()):
                    val = get_tec_for_coords(grid, lat, lon)
                    cols[i].metric(f"VTEC: {city}", f"{val:.2f} TECU")

                # 2. Визуализация карты (общая)
                st.subheader("Карта плотности ионосферы")
                fig, ax = plt.subplots(figsize=(10, 4))
                im = ax.imshow(np.flipud(grid.T), cmap='inferno', extent=[-180, 180, -87.5, 87.5], aspect='auto')
                plt.colorbar(im, label='VTEC (TECU)')
                st.pyplot(fig)

                # 3. Сейсмика (для Алматы как базовой точки)
                quakes = requests.get(
                    "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100").json()
                local_quakes = []
                for f in quakes['features']:
                    lon, lat = f['geometry']['coordinates'][:2]
                    dist = ((lat - 43.25) ** 2 + (lon - 76.92) ** 2) ** 0.5 * 111
                    if dist < 1000 and f['properties']['mag'] > 2.0:
                        local_quakes.append({'place': f['properties']['place'], 'mag': f['properties']['mag']})

                if local_quakes:
                    st.subheader("Сейсмическая активность (радиус 1000 км от Алматы)")
                    df_q = pd.DataFrame(local_quakes)
                    st.bar_chart(df_q.set_index('place')['mag'])
            else:
                st.warning("Нет новых данных NASA.")
    except Exception as e:
        st.error(f"Ошибка: {e}")