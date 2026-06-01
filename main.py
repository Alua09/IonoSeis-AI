import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import requests
import gzip
import shutil
import os
import pandas as pd
import tarfile
from datetime import datetime, timedelta

# Настройка
st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
st.title("🛰 IonoSeis AI: Литосферно-ионосферный мониторинг")

CITIES = {"Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59), "Токио": (35.68, 139.65)}

if 'prev_tec' not in st.session_state:
    st.session_state.prev_tec = {city: 0.0 for city in CITIES}


def setup_auth():
    os.environ['EARTHDATA_USERNAME'] = st.secrets['EARTHDATA_USERNAME']
    os.environ['EARTHDATA_PASSWORD'] = st.secrets['EARTHDATA_PASSWORD']
    return earthaccess.login(strategy="environment")


def safe_extract(file_path):
    """Универсальная распаковка, обрабатывающая ошибки формата"""
    try:
        # Пытаемся стандартным gzip
        with gzip.open(file_path, 'rb') as f_in:
            with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
    except:
        # Если gzip не сработал, пробуем как обычный файл (иногда они уже распакованы)
        shutil.copyfile(file_path, "data.ionex")


def parse_upc_ionex():
    tec = []
    with open("data.ionex", 'r', errors='ignore') as f:
        in_block = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_block = True
            elif 'END OF TEC MAP' in line:
                in_block = False
            elif in_block and not any(x in line for x in ['LAT/LON', 'EPOCH', 'START', 'END']):
                for p in line.split():
                    try:
                        val = float(p); tec.append(val if val < 9000 else 0)
                    except:
                        continue
    return np.array(tec[:5183]).reshape((71, 73))


def get_normalized_tec(grid, lat, lon):
    lat_idx = max(0, min(int((lat + 87.5) / 2.5), 70))
    lon_idx = max(0, min(int((lon + 180) / 5.0), 72))
    raw_val = grid[lat_idx, lon_idx]
    return raw_val / 10.0 if raw_val > 100 else raw_val


# Профессиональное название кнопки
if st.button("📊 ЗАПУСК АНАЛИЗА ТЕКУЩЕГО СОСТОЯНИЯ ИОНОСФЕРЫ"):
    try:
        with st.spinner("Синхронизация с геофизическими узлами..."):
            setup_auth()
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=5), datetime.now()))
            if results:
                if os.path.exists("./tmp"): shutil.rmtree("./tmp")
                os.makedirs("./tmp")

                results.sort(key=lambda x: x['umm']['TemporalExtent']['RangeDateTime']['BeginningDateTime'],
                             reverse=True)
                files = earthaccess.download(results[0:1], "./tmp")

                safe_extract(files[0])  # Используем новую функцию
                grid = parse_upc_ionex()

                start_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
                quakes = requests.get(
                    f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time}").json()

                for city, (c_lat, c_lon) in CITIES.items():
                    st.markdown("---")
                    st.subheader(f"📍 Регион: {city}")
                    val = get_normalized_tec(grid, c_lat, c_lon)

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.metric("VTEC (TECU)", f"{val:.2f}")
                        fig, ax = plt.subplots(figsize=(6, 1))
                        ax.barh(0, val, color='red' if val > 50 else 'skyblue')
                        ax.set_xlim(0, 100)
                        ax.set_xlabel("VTEC (ед. TECU)")
                        ax.axvline(x=50, color='orange', linestyle='--', alpha=0.6)
                        ax.set_yticks([])
                        st.pyplot(fig)

                    with c2:
                        local_q = [f"🔹 {f['properties']['place']} | M: {f['properties']['mag']}"
                                   for f in quakes.get('features', [])
                                   if ((f['geometry']['coordinates'][1] - c_lat) ** 2 +
                                       (f['geometry']['coordinates'][0] - c_lon) ** 2) ** 0.5 * 111 < 1500
                                   and f['properties']['mag'] > 3.0]
                        if local_q:
                            st.write(pd.DataFrame([q.split('|') for q in local_q], columns=['Место', 'Магнитуда']))
                        else:
                            st.info(f"Статус: Геофизический покой (в радиусе 1500 км нет событий > 3.0).")
            else:
                st.warning("Данные IONEX временно отсутствуют.")
    except Exception as e:
        st.error(f"Системная ошибка: {e}")

st.write("Метод мониторинга основан на анализе литосферно-ионосферных связей.")