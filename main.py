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
st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
st.title("🛰 IonoSeis AI: Глобальный мониторинг литосферно-ионосферных связей")

CITIES = {"Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59), "Токио": (35.68, 139.65)}

# Инициализация памяти для динамики
if 'prev_tec' not in st.session_state:
    st.session_state.prev_tec = {city: 0.0 for city in CITIES}


# --- ФУНКЦИИ ---
def setup_auth():
    os.environ['EARTHDATA_USERNAME'] = st.secrets['EARTHDATA_USERNAME']
    os.environ['EARTHDATA_PASSWORD'] = st.secrets['EARTHDATA_PASSWORD']
    return earthaccess.login(strategy="environment")


def parse_upc_ionex(file_path):
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


# --- ИНТЕРФЕЙС ---
if st.button("🚀 АНАЛИЗ VTEC И СЕЙСМИЧЕСКОЙ АКТИВНОСТИ"):
    try:
        with st.spinner("Синхронизация данных..."):
            setup_auth()
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=5), datetime.now()), count=1)

            if results:
                files = earthaccess.download(results, "./tmp")
                grid = parse_upc_ionex(files[0])
                quakes = requests.get(
                    "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100").json()

                for city, (c_lat, c_lon) in CITIES.items():
                    st.markdown("---")
                    st.subheader(f"📍 Регион: {city}")
                    val = get_normalized_tec(grid, c_lat, c_lon)

                    # Расчет динамики
                    delta = val - st.session_state.prev_tec[city]
                    st.session_state.prev_tec[city] = val

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        # Streamlit сам добавит стрелку и цвет:
                        # inverse означает: рост VTEC = красный, падение = зеленый
                        st.metric(
                            label="VTEC (TECU)",
                            value=f"{val:.2f}",
                            delta=f"{delta:.2f}",
                            delta_color="inverse"
                        )
                        fig, ax = plt.subplots(figsize=(6, 1.5))
                        ax.barh(0, val, color='red' if val > 50 else 'skyblue')
                        ax.set_xlim(0, 100)
                        ax.set_xlabel("VTEC (ед. TECU)")
                        ax.axvline(x=50, color='orange', linestyle='--', alpha=0.6)
                        ax.set_yticks([])
                        st.pyplot(fig)

                    with c2:
                        local_q = [f"🔹 {f['properties']['place']} | M: {f['properties']['mag']}"
                                   for f in quakes['features']
                                   if ((f['geometry']['coordinates'][1] - c_lat) ** 2 +
                                       (f['geometry']['coordinates'][0] - c_lon) ** 2) ** 0.5 * 111 < 1500
                                   and f['properties']['mag'] > 3.0]

                        if local_q:
                            st.write(pd.DataFrame([q.split('|') for q in local_q], columns=['Место', 'Магнитуда']))
                        else:
                            st.info(f"Спокойно: в радиусе 1500 км от {city} событий > 3.0 нет.")
            else:
                st.warning("Нет новых данных NASA.")
    except Exception as e:
        st.error(f"Ошибка системы: {e}")

st.write("Метод основан на анализе ионосферных аномалий как предвестников сейсмических событий.")