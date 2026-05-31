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
st.set_page_config(layout="wide", page_title="IonoSeis AI: Анализ")


# --- 1. ПАРСЕР (ОБЯЗАТЕЛЬНО В НАЧАЛЕ) ---
def parse_upc_ionex(file_path):
    # Распаковка .gz
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
    # Преобразуем в массив 71x73
    return np.array(tec_values[:5183]).reshape((71, 73))


# --- 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_vtec_for_coords(grid, lat, lon):
    # Индексы сетки
    lat_idx = int((lat + 87.5) / 2.5)
    lon_idx = int((lon + 180) / 5.0)
    return grid[min(lat_idx, 70), min(lon_idx, 72)]


# --- 3. ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis: Анализ Алматы и Токио")

if st.button("🚀 ПОСТРОИТЬ ГРАФИКИ ПУЛЬСА"):
    try:
        # Авторизация
        earthaccess.login(strategy="netrc")

        # Поиск
        results = earthaccess.search_data(
            short_name='GNSS_IGS_AC_ion_VTEC_comp',
            temporal=(datetime.now() - timedelta(days=2), datetime.now()),
            count=1
        )
        files = earthaccess.download(results, "./tmp")

        # Парсинг
        grid = parse_upc_ionex(files[0])

        # Координаты
        locations = {"Алматы": (43.2, 76.9), "Токио": (35.6, 139.6)}

        # Графики
        fig, ax = plt.subplots(figsize=(10, 6))

        for name, (lat, lon) in locations.items():
            val = get_vtec_for_coords(grid, lat, lon)
            ax.bar(name, val, color='green' if name == "Алматы" else 'blue', alpha=0.7)

        ax.set_ylabel("Уровень VTEC")
        ax.set_title("Сравнение ионосферного фона")
        st.pyplot(fig)

        st.success("Анализ завершен.")

    except Exception as e:
        st.error(f"Ошибка: {e}")