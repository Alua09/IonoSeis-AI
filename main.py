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
st.set_page_config(layout="wide", page_title="IonoSeis AI: Professional Monitor")
st.title("🛰 IonoSeis AI: Анализ литосферно-ионосферной связи")


# --- 1. АВТОРИЗАЦИЯ И ПОИСК ---
def setup_auth():
    # Создаем netrc файл для earthaccess, используя Streamlit Secrets
    netrc_path = os.path.expanduser("~/.netrc")
    with open(netrc_path, "w") as f:
        f.write(
            f"machine urs.earthdata.nasa.gov\nlogin {st.secrets['EARTHDATA_USERNAME']}\npassword {st.secrets['EARTHDATA_PASSWORD']}")
    os.chmod(netrc_path, 0o600)
    earthaccess.login(strategy="netrc")


# --- 2. УЛУЧШЕННЫЙ ПАРСЕР ---
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
                for p in line.split():
                    try:
                        val = float(p)
                        # ФИЛЬТР: оставляем только физически адекватные значения VTEC
                        tec_values.append(val if 0 < val < 300 else np.nan)
                    except:
                        continue

    data = np.array(tec_values, dtype=float)
    # Заполняем пропуски средним значением для корректного отображения карты
    data[np.isnan(data)] = np.nanmean(data)
    return data[:5183].reshape((71, 73))


# --- 3. ИНТЕРФЕЙС ---
if st.button("🚀 ЗАПУСТИТЬ МОНИТОРИНГ И НАЛОЖЕНИЕ ДАННЫХ"):
    try:
        with st.spinner("Синхронизация с серверами NASA и USGS..."):
            setup_auth()
            # Поиск актуальных данных за последние 5 дней
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now() - timedelta(days=5), datetime.now()),
                count=1
            )
            files = earthaccess.download(results, "./tmp")
            grid = parse_upc_ionex(files[0])

            # Визуализация
            fig, ax = plt.subplots(figsize=(12, 6))
            im = ax.imshow(np.flipud(grid.T), cmap='inferno', interpolation='nearest',
                           extent=[-180, 180, -87.5, 87.5], aspect='auto', alpha=0.9)

            # Наложение сейсмики (USGS)
            quakes = requests.get(
                "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=5.5&limit=20").json()
            for f in quakes['features']:
                lon, lat = f['geometry']['coordinates'][:2]
                mag = f['properties']['mag']
                ax.scatter(lon, lat, color='white', marker='*', s=150, edgecolors='black', label=f'Mag {mag}')

            plt.colorbar(im, label='VTEC (TECU)')
            ax.set_title("Глобальная карта VTEC и эпицентры сильных землетрясений")
            st.pyplot(fig)
            st.success("Анализ завершен.")

    except Exception as e:
        st.error(f"Ошибка в процессе синхронизации: {e}")

st.markdown("---")
st.write("Метод основан на выявлении аномалий плотности электронов в ионосфере, вызванных тектоническими процессами.")