import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import gzip
import shutil
import os
from datetime import datetime, timedelta
import earthaccess


# --- 1. ПАРСИНГ ДАННЫХ ДЛЯ ТОЧКИ ---
def get_vtec_for_coords(grid, lat, lon):
    # Конвертация lat/lon в индексы сетки (71x73)
    # Широта от -87.5 до 87.5 (шаг 2.5), Долгота от -180 до 180 (шаг 5)
    lat_idx = int((lat + 87.5) / 2.5)
    lon_idx = int((lon + 180) / 5.0)

    # Берем значение из сетки (с учетом того, что grid - это 71x73)
    return grid[min(lat_idx, 70), min(lon_idx, 72)]


# --- 2. ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis: Пульс ионосферы (Алматы vs Токио)")

if st.button("🚀 ПОСТРОИТЬ ГРАФИКИ ПУЛЬСА"):
    try:
        # (Предполагаем, что файл уже скачан в ./tmp/ через earthaccess)
        grid = parse_upc_ionex("./tmp/UPC0OPSFIN_20261210000_01D_02H_GIM.INX.gz")

        # Координаты городов
        locations = {
            "Алматы": (43.2, 76.9),
            "Токио": (35.6, 139.6)
        }

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        # График для Алматы
        vtec_almaty = get_vtec_for_coords(grid, *locations["Алматы"])
        ax1.plot([vtec_almaty] * 5, label='VTEC Almaty', color='green', marker='o')
        ax1.set_title("Гармоника ионосферы: Алматы")
        ax1.grid(True)

        # График для Токио
        vtec_tokyo = get_vtec_for_coords(grid, *locations["Токио"])
        ax2.plot([vtec_tokyo] * 5, label='VTEC Tokyo', color='blue', marker='o')
        ax2.set_title("Гармоника ионосферы: Токио")
        ax2.grid(True)

        st.pyplot(fig)

        st.write("### Анализ:")
        st.write(f"Текущий уровень VTEC в Алматы: {vtec_almaty:.2f}")
        st.write(f"Текущий уровень VTEC в Токио: {vtec_tokyo:.2f}")

    except Exception as e:
        st.error(f"Ошибка построения графиков: {e}")