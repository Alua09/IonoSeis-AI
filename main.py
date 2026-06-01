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

st.set_page_config(layout="wide", page_title="IonoSeis AI: Global Monitor")
st.title("🛰 IonoSeis AI: Глобальный сейсмо-ионосферный мониторинг")

# Координаты городов (lat, lon)
LOCATIONS = {
    "Алматы": (43.25, 76.92),
    "Бишкек": (42.87, 74.59),
    "Токио": (35.68, 139.65)
}


def get_kp_index():
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
        data = requests.get(url, timeout=5).json()
        return float(data[-1][1])
    except:
        return "N/A"


def get_tec_for_coords(grid, lat, lon):
    # Ionex данные обычно идут с шагом 2.5 по широте и 5.0 по долготе
    lat_idx = int((lat + 87.5) / 2.5)
    lon_idx = int((lon + 180) / 5.0)
    # Защита от выхода за границы
    lat_idx = max(0, min(lat_idx, 70))
    lon_idx = max(0, min(lon_idx, 72))
    return grid[lat_idx, lon_idx]


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ОБНОВИТЬ ГЛОБАЛЬНЫЕ ДАННЫЕ"):
    with st.spinner("Синхронизация..."):
        # 1. Kp-индекс
        kp = get_kp_index()
        st.metric("Глобальный геомагнитный Kp-индекс", kp)

        # 2. Ионосфера
        # (Остальной код загрузки данных earthaccess...)
        # ... (используем parse_upc_ionex из вашего кода) ...

        st.subheader("Сводка по регионам")
        cols = st.columns(len(LOCATIONS))
        for i, (city, (lat, lon)) in enumerate(LOCATIONS.items()):
            tec = get_tec_for_coords(grid, lat, lon)  # grid получен после парсинга
            cols[i].metric(f"VTEC: {city}", f"{tec:.2f} TECU")

st.write("Метод мониторинга основан на японской концепции литосферно-ионосферного сопряжения.")