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

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis AI: Реальный мониторинг")
st.title("🛰 IonoSeis AI: Мониторинг ионосферы и сейсмики")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92


# --- ФУНКЦИИ ---
def get_kp_index():
    """Получение Kp-индекса напрямую из JSON-потока NOAA"""
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
        data = requests.get(url, timeout=10).json()
        return float(data[-1][1])  # Последнее значение
    except:
        return None


def setup_auth():
    # Используйте переменные окружения, настроенные в Secrets Streamlit
    return earthaccess.login(strategy="environment")


def parse_upc_ionex(file_path):
    # Распаковка ionex и парсинг... (ваш код)
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


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ОБНОВИТЬ ВСЕ ДАННЫЕ В МОМЕНТЕ"):
    with st.spinner("Синхронизация с серверами NASA, NOAA и USGS..."):
        # 1. ГЕОМАГНИТНЫЙ ФОН (Kp)
        kp = get_kp_index()
        st.subheader("🌍 Глобальная геомагнитная обстановка")
        if kp:
            st.metric("Kp-индекс (NOAA)", kp)
            if kp >= 5:
                st.error("⚠️ Внимание: Геомагнитная буря! Возможны искажения данных ионосферы.")
            else:
                st.success("Геомагнитный фон в норме.")

        # 2. ИОНОСФЕРА (NASA)
        setup_auth()
        results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', count=1)
        if results:
            files = earthaccess.download(results, "./tmp")
            grid = parse_upc_ionex(files[0])
            val = grid[int((ALMATY_LAT + 87.5) / 2.5), int((ALMATY_LON + 180) / 5.0)]
            st.metric("Плотность ионосферы (VTEC) над Алматы", f"{val:.2f} TECU")

        # 3. СЕЙСМИКА (USGS)
        st.subheader("📉 Сейсмика (Алматы 1000 км)")
        quakes = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=50").json()
        local_quakes = [{'place': f['properties']['place'], 'mag': f['properties']['mag'], 'dist': round(((f[
                                                                                                               'geometry'][
                                                                                                               'coordinates'][
                                                                                                               1] - ALMATY_LAT) ** 2 + (
                                                                                                                      f[
                                                                                                                          'geometry'][
                                                                                                                          'coordinates'][
                                                                                                                          0] - ALMATY_LON) ** 2) ** 0.5 * 111)}
                        for f in quakes['features']]
        local_quakes = [q for q in local_quakes if q['dist'] < 1000 and q['mag'] > 2.0]

        if local_quakes:
            st.bar_chart(pd.DataFrame(local_quakes).set_index('place')['mag'])
        else:
            st.info("Сейсмически спокойно.")