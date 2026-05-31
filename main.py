import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import gzip
import shutil
import os
import requests
from datetime import datetime, timedelta

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis AI: Мониторинг")
st.title("🛰 IonoSeis AI: Анализ ионосферы")


# --- ФУНКЦИЯ ПАРСИНГА ---
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


# --- ФУНКЦИЯ КООРДИНАТ ---
def get_vtec_for_coords(grid, lat, lon):
    lat_idx = int((lat + 87.5) / 2.5)
    lon_idx = int((lon + 180) / 5.0)
    return grid[min(lat_idx, 70), min(lon_idx, 72)]


# --- ОСНОВНАЯ ЛОГИКА ---
if st.button("🚀 ЗАПУСТИТЬ ПОЛНЫЙ ЦИКЛ АНАЛИЗА"):
    try:
        with st.spinner("Авторизация и поиск данных..."):
            # Создаем netrc
            netrc_path = os.path.expanduser("~/.netrc")
            with open(netrc_path, "w") as f:
                f.write(
                    f"machine urs.earthdata.nasa.gov\nlogin {st.secrets['EARTHDATA_USERNAME']}\npassword {st.secrets['EARTHDATA_PASSWORD']}")
            os.chmod(netrc_path, 0o600)
            earthaccess.login(strategy="netrc")

            # Поиск
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now() - timedelta(days=10), datetime.now()),
                count=1
            )

            if not results:
                st.error("Данные не найдены. Проверьте настройки коллекции в Earthdata Search.")
                st.stop()

            # Скачивание
            files = earthaccess.download(results, "./tmp")
            if not files:
                st.error("Ошибка: список скачанных файлов пуст.")
                st.stop()

            grid = parse_upc_ionex(files[0])

            # Визуализация
            locations = {"Алматы": (43.2, 76.9), "Токио": (35.6, 139.6)}
            fig, ax = plt.subplots(figsize=(10, 5))

            names = list(locations.keys())
            values = [get_vtec_for_coords(grid, *coords) for coords in locations.values()]

            ax.bar(names, values, color=['green', 'blue'], alpha=0.7)
            ax.set_title("Уровень VTEC: Алматы vs Токио")
            ax.set_ylabel("VTEC Units")

            st.pyplot(fig)
            st.success("Анализ завершен успешно!")

    except Exception as e:
        st.error(f"Критическая ошибка: {e}")