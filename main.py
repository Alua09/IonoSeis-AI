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

# Настройка
st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
st.title("🛰 IonoSeis AI: Литосферно-ионосферный мониторинг")

CITIES = {"Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59), "Токио": (35.68, 139.65)}


def setup_auth():
    os.environ['EARTHDATA_USERNAME'] = st.secrets['EARTHDATA_USERNAME']
    os.environ['EARTHDATA_PASSWORD'] = st.secrets['EARTHDATA_PASSWORD']
    return earthaccess.login(strategy="environment")


def parse_upc_ionex_accurate():
    """Более точный парсер для формата IONEX"""
    grid = np.zeros((71, 73))
    with open("data.ionex", 'r', errors='ignore') as f:
        lines = f.readlines()

    # Ищем блок данных
    i = 0
    while i < len(lines):
        if 'START OF TEC MAP' in lines[i]:
            i += 1
            # В блоке TEC MAP данные идут по 2 строки на широту
            for lat_idx in range(71):
                # Читаем строку с данными
                line = lines[i].split()
                # В IONEX данные TEC — это целые числа, которые надо поделить на 10
                for lon_idx in range(len(line)):
                    if lon_idx < 73:
                        grid[lat_idx, lon_idx] = float(line[lon_idx]) / 10.0
                i += 1
            break
        i += 1
    return grid


if st.button("📊 АНАЛИЗ ИОНОСФЕРНЫХ ДАННЫХ"):
    try:
        with st.spinner("Загрузка и обработка..."):
            setup_auth()
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=5), datetime.now()))
            if results:
                files = earthaccess.download(results[0:1], "./tmp")
                # Распаковка
                with gzip.open(files[0], 'rb') as f_in:
                    with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)

                grid = parse_upc_ionex_accurate()

                # Запрос событий
                start_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
                quakes = requests.get(
                    f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time}").json()

                for city, (c_lat, c_lon) in CITIES.items():
                    st.markdown("---")
                    st.subheader(f"📍 {city}")

                    # Индексы для сетки IONEX (-87.5:2.5:87.5 и -180:5:180)
                    lat_i = int((c_lat + 87.5) / 2.5)
                    lon_i = int((c_lon + 180) / 5.0)
                    val = grid[lat_i, lon_i]

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.metric("VTEC (TECU)", f"{val:.1f}")
                        fig, ax = plt.subplots(figsize=(6, 1))
                        ax.barh(0, val, color='red' if val > 40 else 'skyblue')
                        ax.set_xlim(0, 100)
                        st.pyplot(fig)
                    with c2:
                        # Логика поиска событий
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
        st.error(f"Ошибка: {e}")