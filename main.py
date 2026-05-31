import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import gzip
import shutil
import os
import requests
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Динамика")
st.title("🛰 IonoSeis AI: Временной ряд VTEC (Алматы vs Токио)")


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


def get_vtec(grid, lat, lon):
    lat_idx = int((lat + 87.5) / 2.5)
    lon_idx = int((lon + 180) / 5.0)
    return grid[min(lat_idx, 70), min(lon_idx, 72)]


if st.button("🚀 ПОСТРОИТЬ ГАРМОНИКИ (ЗА НЕДЕЛЮ)"):
    with st.spinner("Анализирую историю за 7 дней..."):
        try:
            # 1. Авторизация
            earthaccess.login(strategy="netrc")

            # 2. Ищем 7 последних файлов
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now() - timedelta(days=7), datetime.now()),
                count=7
            )
            files = earthaccess.download(results, "./tmp")
            files.sort()  # Сортируем по времени

            # 3. Извлекаем временной ряд
            almaty_series, tokyo_series = [], []
            for f in files:
                grid = parse_upc_ionex(f)
                almaty_series.append(get_vtec(grid, 43.2, 76.9))
                tokyo_series.append(get_vtec(grid, 35.6, 139.6))

            # 4. Строим ГАРМОНИЧЕСКИЙ ГРАФИК
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(almaty_series, label='Алматы (VTEC)', marker='o', color='green', linewidth=2)
            ax.plot(tokyo_series, label='Токио (VTEC)', marker='s', color='blue', linewidth=2)

            ax.set_title("Динамика ионосферы: Гармонический анализ за неделю")
            ax.set_xlabel("Дни назад")
            ax.set_ylabel("VTEC Units")
            ax.legend()
            ax.grid(True, linestyle='--', alpha=0.6)

            st.pyplot(fig)
            st.success("Линии построены! Теперь вы видите, как 'дышит' ионосфера.")

        except Exception as e:
            st.error(f"Ошибка построения графиков: {e}")