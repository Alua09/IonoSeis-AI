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
st.set_page_config(layout="wide", page_title="IonoSeis AI: Алматы")
st.title("🛰 IonoSeis AI: Глубокий анализ ионосферы")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92


# --- ФУНКЦИИ ---
def setup_auth():
    os.environ['EARTHDATA_USERNAME'] = st.secrets['EARTHDATA_USERNAME']
    os.environ['EARTHDATA_PASSWORD'] = st.secrets['EARTHDATA_PASSWORD']
    return earthaccess.login(strategy="environment")


def parse_upc_ionex(file_path):
    # Распаковка и парсинг
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


def get_almaty_tec(grid):
    lat_idx = int((ALMATY_LAT + 87.5) / 2.5)
    lon_idx = int((ALMATY_LON + 180) / 5.0)
    return grid[lat_idx, lon_idx]


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ЗАПУСТИТЬ АНАЛИЗ (NASA + USGS)"):
    try:
        with st.spinner("Связь с серверами NASA..."):
            setup_auth()
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now() - timedelta(days=5), datetime.now()),
                count=1
            )

            if results and len(results) > 0:
                files = earthaccess.download(results, "./tmp")
                if files:
                    grid = parse_upc_ionex(files[0])
                    val = get_almaty_tec(grid)

                    st.metric("Плотность ионосферы над Алматы (VTEC)", f"{val:.2f} TECU")

                    # USGS Сейсмика
                    quakes = requests.get(
                        "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=10").json()
                    st.subheader("Последние сейсмические события")
                    for f in quakes['features'][:5]:
                        st.write(f"- {f['properties']['place']} | Магнитуда: {f['properties']['mag']}")

                    st.success("Данные успешно обновлены.")
                else:
                    st.error("Ошибка при скачивании файла данных.")
            else:
                st.warning("Нет новых данных от NASA за последние 5 дней.")

    except Exception as e:
        st.error(f"Ошибка процесса: {e}")

st.sidebar.markdown("---")
st.sidebar.write("### Статус: Подключен")
st.sidebar.write("Регион мониторинга: Алматы")