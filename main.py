import streamlit as st
import requests
import gzip
import shutil
import numpy as np
import pandas as pd


# 1. ОБЯЗАТЕЛЬНОЕ ОПРЕДЕЛЕНИЕ ФУНКЦИИ
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


# 2. ФУНКЦИЯ ДЛЯ ВЫЗОВА
def get_almaty_tec(grid):
    ALMATY_LAT, ALMATY_LON = 43.25, 76.92
    lat_idx = int((ALMATY_LAT + 87.5) / 2.5)
    lon_idx = int((ALMATY_LON + 180) / 5.0)
    return grid[lat_idx, lon_idx]


# 3. ОСНОВНОЙ КОД
st.title("🛰 IonoSeis AI: Конкурсный мониторинг")

if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    try:
        # Ваш вызов, который выдавал ошибку
        file_path = "data.ionex.gz"  # Убедитесь, что файл скачан
        grid = parse_upc_ionex(file_path)
        val = get_almaty_tec(grid)
        st.metric("Плотность VTEC", f"{val:.2f} TECU")
    except NameError as ne:
        st.error(f"Ошибка имени (NameError): {ne}. Проверьте порядок функций в коде.")
    except Exception as e:
        st.error(f"Ошибка: {e}")