import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import gzip
import shutil
import os
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Анализ")
st.title("🛰 IonoSeis AI: Гармоники ионосферы")


def parse_ionex_any_file(file_path):
    # Превращаем путь в строку, чтобы работали методы строк
    path_str = str(file_path)

    # Если файл сжат .gz
    if path_str.endswith('.gz'):
        with gzip.open(path_str, 'rb') as f_in:
            with open("temp_data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
        target = "temp_data.ionex"
    else:
        target = path_str

    tec_values = []
    with open(target, 'r', errors='ignore') as f:
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


def get_vtec(grid, lat, lon):
    lat_idx = int((lat + 87.5) / 2.5)
    lon_idx = int((lon + 180) / 5.0)
    return grid[min(lat_idx, 70), min(lon_idx, 72)]


if st.button("🚀 ЗАПУСК: АНАЛИЗ ДАННЫХ"):
    try:
        earthaccess.login(strategy="netrc")
        results = earthaccess.search_data(
            short_name='GNSS_IGS_AC_ion_VTEC_comp',
            temporal=(datetime.now() - timedelta(days=7), datetime.now()),
            count=5
        )
        # Скачиваем в текущую папку
        paths = earthaccess.download(results, ".")

        almaty_series, tokyo_series = [], []
        for f in paths:
            grid = parse_ionex_any_file(f)
            almaty_series.append(get_vtec(grid, 43.2, 76.9))
            tokyo_series.append(get_vtec(grid, 35.6, 139.6))

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(almaty_series, label='Алматы', marker='o', color='green')
        ax.plot(tokyo_series, label='Токио', marker='s', color='blue')
        ax.set_title("Динамика ионосферы: Гармонический пульс")
        ax.legend();
        ax.grid(True)
        st.pyplot(fig)
        st.success("Анализ выполнен!")

    except Exception as e:
        st.error(f"Ошибка: {e}")