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

st.set_page_config(layout="wide", page_title="IonoSeis AI: Экспертная система")
st.title("🛰 IonoSeis AI: Мониторинг литосферно-ионосферных аномалий")

CITIES = {"Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59), "Токио": (35.68, 139.65)}


def get_status_text(val):
    if val < 10: return "🟢 Стабильное состояние ионосферы. Фоновые значения VTEC находятся в пределах нормы."
    if 10 <= val < 30: return "🟡 Повышенная активность. Возможны слабые колебания электронной плотности."
    return "🔴 АНОМАЛЬНАЯ АКТИВНОСТЬ. Зафиксированы отклонения, характерные для предсейсмических процессов."


def setup_auth():
    os.environ['EARTHDATA_USERNAME'] = st.secrets['EARTHDATA_USERNAME']
    os.environ['EARTHDATA_PASSWORD'] = st.secrets['EARTHDATA_PASSWORD']
    return earthaccess.login(strategy="environment")


def parse_ionex_final():
    grid = np.zeros((71, 73))
    lat_idx, lon_idx = 0, 0
    with open("data.ionex", 'r', errors='ignore') as f:
        in_map = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_map = True
            elif 'END OF TEC MAP' in line:
                in_map = False
            elif in_map:
                for p in line.split():
                    try:
                        val = float(p)
                        if 0 <= val < 9000:
                            grid[lat_idx, lon_idx] = val / 10.0
                            lon_idx += 1
                            if lon_idx == 73: lon_idx = 0; lat_idx += 1
                    except:
                        continue
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


if st.button("🔄 ОБНОВИТЬ ГЕОФИЗИЧЕСКИЙ ОТЧЕТ"):
    try:
        with st.spinner("Анализ спутниковых данных IGS и сейсмических сводок USGS..."):
            setup_auth()
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=2), datetime.now()))
            if results:
                files = earthaccess.download(results[0:1], "./tmp")
                with gzip.open(files[0], 'rb') as f_in:
                    with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
                grid = parse_ionex_grid() if 'parse_ionex_grid' in globals() else parse_ionex_final()

                # Свежие данные USGS за 24 часа
                start_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
                quakes = requests.get(
                    f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time}").json()

                for city, (c_lat, c_lon) in CITIES.items():
                    st.markdown("---")
                    st.subheader(f"📍 Станция мониторинга: {city}")
                    val = get_interp_tec(grid, c_lat, c_lon)

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.metric("VTEC (TECU)", f"{val:.2f}")
                        st.write(get_status_text(val))
                    with c2:
                        # Фильтр событий в радиусе 1000 км
                        local_q = [f"Magnitude {f['properties']['mag']} | {f['properties']['place']}"
                                   for f in quakes.get('features', [])
                                   if ((f['geometry']['coordinates'][1] - c_lat) ** 2 +
                                       (f['geometry']['coordinates'][0] - c_lon) ** 2) ** 0.5 < 9]

                        if local_q:
                            st.error("⚠️ Сейсмическая активность в радиусе 1000 км:")
                            for q in local_q: st.write(q)
                        else:
                            st.success("✅ Сейсмический фон в радиусе 1000 км без существенных отклонений.")
            else:
                st.warning("Серверы IGS обновляются. Повторите запрос через 5 минут.")
    except Exception as e:
        st.error(f"Ошибка системы: {e}")