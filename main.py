import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import requests
import gzip
import shutil
import os
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: KZ Monitor")
st.title("🛰 IonoSeis AI: Анализ ионосферы Казахстана")


# --- ФУНКЦИИ ---
def setup_auth():
    netrc_path = os.path.expanduser("~/.netrc")
    with open(netrc_path, "w") as f:
        f.write(
            f"machine urs.earthdata.nasa.gov\nlogin {st.secrets['EARTHDATA_USERNAME']}\npassword {st.secrets['EARTHDATA_PASSWORD']}")
    os.chmod(netrc_path, 0o600)
    earthaccess.login(strategy="netrc")


def parse_and_clean(file_path):
    with gzip.open(file_path, 'rb') as f_in:
        with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)

    tec = []
    with open("data.ionex", 'r', errors='ignore') as f:
        in_block = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_block = True
            elif 'END OF TEC MAP' in line:
                in_block = False
            elif in_block and not any(x in line for x in ['LAT/LON', 'EPOCH']):
                for p in line.split():
                    try:
                        val = float(p)
                        # Фильтр: 0-200 TECU (реалистичный диапазон)
                        tec.append(val if 0 < val < 200 else np.nan)
                    except:
                        continue

    data = np.array(tec, dtype=float)
    data[np.isnan(data)] = np.nanmean(data)  # Заполнение пропусков
    return data[:5183].reshape((71, 73))


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ЗАПУСТИТЬ АНАЛИЗ КАЗАХСТАНА"):
    try:
        with st.spinner("Синхронизация данных..."):
            setup_auth()
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', count=1)
            files = earthaccess.download(results, "./tmp")
            grid = parse_and_clean(files[0])

            # Визуализация с фокусом на РК
            fig, ax = plt.subplots(figsize=(10, 6))
            im = ax.imshow(np.flipud(grid.T), cmap='inferno', interpolation='bicubic',
                           extent=[-180, 180, -87.5, 87.5], aspect='auto', alpha=0.9)

            # Фокус на Казахстан и Центральную Азию
            ax.set_xlim(40, 95)
            ax.set_ylim(35, 60)

            # Сейсмические события
            quakes = requests.get(
                "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=5&limit=10").json()
            for f in quakes['features']:
                lon, lat = f['geometry']['coordinates'][:2]
                ax.scatter(lon, lat, color='white', marker='*', s=100, edgecolors='black')

            plt.colorbar(im, label='VTEC (TECU)')
            ax.set_title("Карта VTEC: Казахстан и сейсмические эпицентры")
            st.pyplot(fig)
            st.success("Анализ региона завершен.")
    except Exception as e:
        st.error(f"Ошибка: {e}")

st.markdown("---")
st.write(
    "Механизм: локальный анализ ионосферных аномалий над территорией Казахстана для сейсмического прогнозирования.")