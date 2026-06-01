import streamlit as st
import earthaccess
import numpy as np
import requests
import gzip
import shutil
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
CITIES = {"Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59), "Токио": (35.68, 139.65)}


def get_kp_index():
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
        data = requests.get(url, timeout=5).json()
        return float(data[-1][1])
    except:
        return 2.0


def parse_ionex_data():
    grid = np.zeros((71, 73))
    lat_idx = 0
    if not os.path.exists("data.ionex"): return grid
    with open("data.ionex", 'r', errors='ignore') as f:
        in_map = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_map = True
            elif 'END OF TEC MAP' in line:
                in_map = False
            elif in_map:
                parts = line.split()
                vals = [float(p) for p in parts if p.replace('.', '').replace('-', '').isdigit() and '-' not in p[1:]]
                if len(vals) >= 10:
                    for lon_idx, val in enumerate(vals):
                        if lon_idx < 73 and lat_idx < 71: grid[lat_idx, lon_idx] = val / 10.0
                    lat_idx += 1
    return grid


st.title("🛰 IonoSeis AI: Экспертный мониторинг")

if st.button("🔄 ЗАПУСК АНАЛИЗА"):
    try:
        with st.spinner("Поиск данных на серверах NASA..."):
            earthaccess.login(strategy="environment")
            # Расширяем поиск до 10 дней, чтобы точно найти хоть что-то
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now() - timedelta(days=10), datetime.now())
            )

            # ПРОВЕРКА: Если список пуст, не идем в download
            if not results or len(results) == 0:
                st.error("Данные не найдены на сервере. Попробуйте сменить параметры или дату.")
            else:
                st.write(f"Найдено гранул: {len(results)}. Скачивание...")
                files = earthaccess.download(results[0:1], "./tmp")

                # Убедимся, что files - это список и он не пуст
                if files and len(files) > 0:
                    try:
                        with gzip.open(files[0], 'rb') as f_in:
                            with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
                    except:
                        shutil.copyfile(files[0], "data.ionex")

                    grid = parse_ionex_data()
                    kp = get_kp_index()
                    # ... остальная логика вывода ...
                    st.success("Данные успешно обработаны!")
                else:
                    st.error("Ошибка при скачивании файла.")

    except Exception as e:
        st.error(f"Системная ошибка: {e}")