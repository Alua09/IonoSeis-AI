import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import requests
import gzip
import shutil
import os
from datetime import datetime, timedelta

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis AI: Система мониторинга")
st.title("🛰 IonoSeis AI: Анализ ионосферы и сейсмоактивности")


# --- 1. АВТОРИЗАЦИЯ И ПОИСК ---
def setup_auth():
    # Создаем netrc файл для earthaccess (берет данные из Secrets)
    netrc_path = os.path.expanduser("~/.netrc")
    with open(netrc_path, "w") as f:
        f.write(
            f"machine urs.earthdata.nasa.gov\nlogin {st.secrets['EARTHDATA_USERNAME']}\npassword {st.secrets['EARTHDATA_PASSWORD']}")
    os.chmod(netrc_path, 0o600)
    earthaccess.login(strategy="netrc")


# --- 2. ПАРСЕР IONEX ---
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
    return np.array(tec_values[:5183]).reshape((71, 73))


# --- 3. ОСНОВНОЙ ИНТЕРФЕЙС ---
if st.button("🚀 ОБНОВИТЬ КАРТУ (NASA + USGS)"):
    try:
        with st.spinner("Синхронизация данных..."):
            setup_auth()
            # Поиск файла
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now() - timedelta(days=5), datetime.now()),
                count=1
            )
            files = earthaccess.download(results, "./tmp")

            # Парсинг
            grid = parse_upc_ionex(files[0])

            # Визуализация
            fig, ax = plt.subplots(figsize=(12, 6))
            im = ax.imshow(np.flipud(grid.T), cmap='jet', interpolation='bicubic',
                           extent=[-180, 180, -87.5, 87.5], aspect='auto', alpha=0.8)

            # Наложение землетрясений (USGS)
            quakes = requests.get(
                "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=5&limit=20").json()
            for f in quakes['features']:
                lon, lat = f['geometry']['coordinates'][:2]
                ax.scatter(lon, lat, color='white', marker='*', s=120, edgecolors='black', label='EQ (>5.0)')

            # Наложение аномалий (VTEC > 700)
            anom_y, anom_x = np.where(grid.T > 700)
            ax.scatter((anom_x * (360 / 73) - 180), (anom_y * (175 / 71) - 87.5),
                       color='red', s=10, alpha=0.5, label='Аномалия')

            plt.colorbar(im, label='VTEC')
            ax.set_title("Глобальная карта: Ионосфера vs Сейсмические события")
            st.pyplot(fig)
            st.success("Данные успешно синхронизированы.")

    except Exception as e:
        st.error(f"Ошибка процесса: {e}")