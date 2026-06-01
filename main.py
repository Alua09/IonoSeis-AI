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
st.set_page_config(layout="wide", page_title="IonoSeis AI: Экспертная панель")

# Глобальные параметры
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


st.title("🛰 IonoSeis AI: Литосферно-ионосферный мониторинг")
st.markdown("---")

if st.button("🔄 ОБНОВИТЬ ДАННЫЕ В РЕАЛЬНОМ ВРЕМЕНИ"):
    with st.spinner("Анализ глобальных данных..."):
        # (Логика скачивания та же)
        earthaccess.login(strategy="environment")
        results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                          temporal=(datetime.now() - timedelta(days=2), datetime.now()))
        files = earthaccess.download(results[0:1], "./tmp")
        try:
            with gzip.open(files[0], 'rb') as f_in:
                with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
        except:
            shutil.copyfile(files[0], "data.ionex")

        grid = parse_ionex_data()
        kp = get_kp_index()

        # Дизайн панели
        col1, col2, col3 = st.columns(3)
        col1.metric("Планетарный Kp-индекс", f"{kp}", delta_color="inverse")
        col2.metric("Статус ионосферы", "Стабильно" if kp < 4 else "Возмущено")
        col3.metric("Источник", "IGS / NOAA / USGS")

        st.markdown("---")

        # Вывод по городам с графиками
        for city, (c_lat, c_lon) in CITIES.items():
            lat_i, lon_i = int((c_lat + 87.5) / 2.5), int((c_lon + 180) / 5.0)
            val = grid[lat_i, lon_i] if grid[lat_i, lon_i] != 0 else 12.0

            # Генерация графика
            fig, ax = plt.subplots(figsize=(8, 2))
            x = np.linspace(0, 10, 50)
            y = np.full(50, 12.0)  # Базовая линия
            y_data = np.full(50, val)  # Ваше значение

            ax.plot(x, y, color='gray', linestyle='--', label='Норма')
            ax.plot(x, y_data, color='skyblue', linewidth=3, label='Текущее VTEC')
            ax.fill_between(x, y_data, color='skyblue', alpha=0.3)
            ax.set_ylim(0, 50)
            ax.legend()
            ax.set_title(f"Профиль VTEC: {city}")

            c_left, c_right = st.columns([1, 2])
            c_left.subheader(f"📍 {city}")
            c_left.metric("VTEC (TECU)", f"{val:.2f}")
            c_right.pyplot(fig)