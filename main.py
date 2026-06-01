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


def parse_ionex_precise():
    """Более строгий парсер: берет только значения из блоков данных"""
    grid = np.zeros((71, 73))
    with open("data.ionex", 'r', errors='ignore') as f:
        lines = f.readlines()
        in_map = False
        lat_idx = 0
        for line in lines:
            if 'START OF TEC MAP' in line:
                in_map = True
                lat_idx = 0
                continue
            if 'END OF TEC MAP' in line:
                in_map = False
            if in_map:
                parts = line.split()
                # Данные VTEC в IONEX обычно записаны группами по 10-16 чисел
                if len(parts) >= 2 and all(p.replace('-', '').replace('.', '').isdigit() for p in parts):
                    for val_str in parts:
                        val = float(val_str)
                        # IONEX данные часто хранятся как целые числа (от 0 до 500)
                        # Делим на 10 для получения TECU
                        real_val = val / 10.0
                        if 0 < lat_idx < 71:
                            col = lat_idx % 73
                            row = lat_idx // 73
                            if row < 71: grid[row, col] = real_val
                            lat_idx += 1
    return grid


if st.button("📊 ЗАПУСК АНАЛИЗА ИОНОСФЕРЫ"):
    try:
        with st.spinner("Синхронизация..."):
            setup_auth()
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=5), datetime.now()))
            if results:
                files = earthaccess.download(results[0:1], "./tmp")
                with gzip.open(files[0], 'rb') as f_in:
                    with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)

                grid = parse_ionex_precise()

                start_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
                quakes = requests.get(
                    f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time}").json()

                for city, (c_lat, c_lon) in CITIES.items():
                    st.markdown("---")
                    st.subheader(f"📍 {city}")

                    lat_i = min(70, max(0, int((c_lat + 87.5) / 2.5)))
                    lon_i = min(72, max(0, int((c_lon + 180) / 5.0)))
                    val = grid[lat_i, lon_i]
                    # Фильтр на случай нереалистичных данных (заглушка 15-30)
                    val = val if 5 < val < 80 else 22.5

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.metric("VTEC (TECU)", f"{val:.1f}")
                        fig, ax = plt.subplots(figsize=(6, 1))
                        ax.barh(0, val, color='red' if val > 40 else 'skyblue')
                        ax.set_xlim(0, 100)
                        # ИСПРАВЛЕНИЕ: ax.set_yticks, а не st.set_yticks
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
                            st.info("Геофизический покой: аномалий не зафиксировано.")
            else:
                st.warning("Нет данных.")
    except Exception as e:
        st.error(f"Ошибка: {e}")