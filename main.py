import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import os
import subprocess
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Анализ")
st.title("🛰 IonoSeis AI: Гармоники ионосферы")


def parse_ionex_universal(file_path):
    # Пытаемся распаковать через системную утилиту 'uncompress' или 'gunzip'
    # .Z файлы — это формат 'compress', для него нужна команда uncompress
    try:
        subprocess.run(["uncompress", "-f", file_path], check=True)
        # После распаковки файл теряет расширение .Z
        file_path = file_path.replace(".Z", "")
    except:
        pass  # Если файл уже не сжат или uncompress нет, идем дальше

    tec_values = []
    with open(file_path, 'r', errors='ignore') as f:
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


if st.button("🚀 ПОСТРОИТЬ ГРАФИКИ (УНИВЕРСАЛЬНЫЙ МЕТОД)"):
    with st.spinner("Обработка архивов..."):
        try:
            earthaccess.login(strategy="netrc")
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now() - timedelta(days=7), datetime.now()),
                count=7
            )
            files = earthaccess.download(results, "./tmp")

            almaty_series, tokyo_series = [], []
            for f in files:
                grid = parse_ionex_universal(f)
                almaty_series.append(get_vtec(grid, 43.2, 76.9))
                tokyo_series.append(get_vtec(grid, 35.6, 139.6))

            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(almaty_series, label='Алматы', marker='o', color='green', linewidth=2)
            ax.plot(tokyo_series, label='Токио', marker='s', color='blue', linewidth=2)
            ax.set_title("Гармонический пульс ионосферы")
            ax.legend();
            ax.grid(True)
            st.pyplot(fig)
            st.success("Данные успешно обработаны!")
        except Exception as e:
            st.error(f"Ошибка парсинга: {e}")