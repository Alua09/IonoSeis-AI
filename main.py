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

st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
st.title("🛰 IonoSeis AI: Литосферно-ионосферный мониторинг")

CITIES = {"Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59), "Токио": (35.68, 139.65)}


def setup_auth():
    os.environ['EARTHDATA_USERNAME'] = st.secrets['EARTHDATA_USERNAME']
    os.environ['EARTHDATA_PASSWORD'] = st.secrets['EARTHDATA_PASSWORD']
    return earthaccess.login(strategy="environment")


def parse_ionex_grid():
    """Парсер, который игнорирует текстовые заголовки и читает только данные VTEC"""
    grid = np.zeros((71, 73))
    lat_idx = 0
    with open("data.ionex", 'r', errors='ignore') as f:
        in_map = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_map = True
                continue
            if 'END OF TEC MAP' in line:
                in_map = False
                continue

            if in_map:
                # Разбиваем строку и пытаемся найти числа
                parts = line.split()
                # Проверка: если в строке есть хотя бы одно число и нет букв
                # (IONEX данные - это числа, заголовки содержат метки типа EPOCH)
                is_data_line = True
                for p in parts:
                    # Если часть строки - не число, считаем это заголовком
                    if not p.replace('.', '', 1).replace('-', '', 1).isdigit():
                        is_data_line = False
                        break

                if is_data_line and len(parts) > 5:
                    if lat_idx < 71:
                        for lon_idx, p in enumerate(parts):
                            if lon_idx < 73:
                                grid[lat_idx, lon_idx] = float(p) / 10.0
                        lat_idx += 1
    return grid


def get_interp_tec(grid, lat, lon):
    lat_f = (lat + 87.5) / 2.5
    lon_f = (lon + 180) / 5.0
    x, y = int(lat_f), int(lon_f)
    x1, y1 = min(x, 70), min(y, 72)
    x2, y2 = min(x + 1, 70), min(y + 1, 72)
    dx, dy = lat_f - x, lon_f - y
    val = (1 - dx) * (1 - dy) * grid[x1, y1] + dx * (1 - dy) * grid[x2, y1] + (1 - dx) * dy * grid[x1, y2] + dx * dy * \
          grid[x2, y2]
    return val


if st.button("📊 ЗАПУСК АНАЛИЗА ИОНОСФЕРЫ"):
    try:
        with st.spinner("Синхронизация данных..."):
            setup_auth()
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=5), datetime.now()))
            if results:
                files = earthaccess.download(results[0:1], "./tmp")
                with gzip.open(files[0], 'rb') as f_in:
                    with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)

                grid = parse_ionex_grid()

                start_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
                quakes = requests.get(
                    f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time}").json()

                for city, (c_lat, c_lon) in CITIES.items():
                    st.markdown("---")
                    st.subheader(f"📍 {city}")
                    val = get_interp_tec(grid, c_lat, c_lon)

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.metric("VTEC (TECU)", f"{val:.2f}")
                        fig, ax = plt.subplots(figsize=(6, 1))
                        ax.barh(0, val, color='red' if val > 30 else 'skyblue')
                        ax.set_xlim(0, 100)
                        ax.set_yticks([])
                        st.pyplot(fig)
                    with c2:
                        local_q = [f"🔹 {f['properties']['place']} | M: {f['properties']['mag']}"
                                   for f in quakes.get('features', [])
                                   if ((f['geometry']['coordinates'][1] - c_lat) ** 2 +
                                       (f['geometry']['coordinates'][0] - c_lon) ** 2) ** 0.5 < 15]
                        if local_q:
                            st.write(pd.DataFrame([q.split('|') for q in local_q], columns=['Место', 'Магнитуда']))
                        else:
                            st.info("Геофизический покой.")
            else:
                st.warning("Нет данных.")
    except Exception as e:
        st.error(f"Ошибка парсинга: {e}")

st.write("Метод использует билинейную интерполяцию сетки IONEX для высокоточной оценки VTEC.")