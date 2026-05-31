import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import earthaccess
import gzip
import shutil
import requests
import os
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Global Monitor")


# --- 1. ФУНКЦИИ ДАННЫХ ---
def get_earthquakes():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {"format": "geojson", "minmagnitude": 5.0, "limit": 20}
    data = requests.get(url, params=params).json()
    return [(f['geometry']['coordinates'][1], f['geometry']['coordinates'][0]) for f in data['features']]


def parse_ionex(file_path):
    tec_values = []
    with open(file_path, 'r') as f:
        in_block = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_block = True
            elif 'END OF TEC MAP' in line:
                in_block = False
            elif in_block and 'LAT/LON1/LON2' not in line:
                for p in line.split():
                    try:
                        val = float(p)
                        if val < 9000: tec_values.append(val)
                    except:
                        continue
    return np.array(tec_values[:5183]).reshape((71, 73))


# --- 2. ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Глобальный мониторинг")
if st.button("🚀 ОБНОВИТЬ КАРТУ (NASA + USGS)"):
    with st.spinner("Загрузка данных..."):
        # Скачивание NASA
        results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', count=1)
        session = earthaccess.login(persist=True).get_session()
        response = session.get(results[0].data_links()[0], stream=True)
        with open("data.ionex.gz", 'wb') as f: f.write(response.content)
        with gzip.open("data.ionex.gz", 'rb') as f_in:
            with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)

        # Обработка
        grid = parse_ionex("data.ionex")
        final_grid = np.flipud(grid)

        # Визуализация
        fig, ax = plt.subplots(figsize=(12, 6))
        im = ax.imshow(final_grid, cmap='jet', interpolation='bicubic',
                       extent=[-180, 180, -87.5, 87.5], aspect='auto')
        plt.colorbar(im, label='VTEC')

        # Наложение аномалий (VTEC > 40)
        anomalies = np.argwhere(final_grid > 40)
        # Преобразование индексов в координаты
        lat_anom = 87.5 - (anomalies[:, 0] * (175 / 71))
        lon_anom = -180 + (anomalies[:, 1] * (360 / 73))
        ax.scatter(lon_anom, lat_anom, color='white', s=1, alpha=0.3, label='Высокий VTEC')

        # Землетрясения
        quakes = get_earthquakes()
        for lat, lon in quakes:
            ax.scatter(lon, lat, color='red', marker='*', s=100, edgecolors='black', label='EQ (>5.0)')

        ax.set_title("Глобальная ионосферная карта и сейсмические события")
        st.pyplot(fig)