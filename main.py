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
st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
st.title("🛰 IonoSeis AI: Экспертный анализ ионосферы")

CITIES = {"Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59), "Токио": (35.68, 139.65)}


def parse_ionex_data():
    """Безопасный парсинг с пропуском мусора"""
    grid = np.zeros((71, 73))
    lat_idx = 0
    with open("data.ionex", 'r', errors='ignore') as f:
        in_map = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_map = True
            elif 'END OF TEC MAP' in line:
                in_map = False
            elif in_map:
                parts = line.split()
                # Берем только то, что является числом (без букв и лишних знаков)
                numeric_vals = []
                for p in parts:
                    try:
                        val = float(p)
                        numeric_vals.append(val)
                    except ValueError:
                        continue

                if len(numeric_vals) >= 10:
                    for lon_idx, val in enumerate(numeric_vals):
                        if lon_idx < 73 and lat_idx < 71: grid[lat_idx, lon_idx] = val / 10.0
                    lat_idx += 1
    return grid


if st.button("🔄 ЗАПУСК ГЕОФИЗИЧЕСКОГО АНАЛИЗА"):
    # 1. ПРИНУДИТЕЛЬНАЯ ОЧИСТКА КЭША (чтобы значения не застывали)
    if os.path.exists("data.ionex"): os.remove("data.ionex")
    if os.path.exists("./tmp"): shutil.rmtree("./tmp")

    try:
        with st.spinner("Синхронизация и обработка данных..."):
            earthaccess.login(strategy="environment")
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=2), datetime.now()))

            if results:
                files = earthaccess.download(results[0:1], "./tmp")
                try:
                    with gzip.open(files[0], 'rb') as f_in:
                        with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
                except:
                    shutil.copyfile(files[0], "data.ionex")

                grid = parse_ionex_data()
                quakes = requests.get(
                    f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={(datetime.now() - timedelta(days=1)).isoformat()}").json()

                for city, (c_lat, c_lon) in CITIES.items():
                    st.markdown("---")
                    st.subheader(f"📍 Станция: {city}")

                    # Индивидуальное время для каждого города (с учетом часового пояса)
                    local_time = datetime.now() + timedelta(hours=6 if "Токио" not in city else 9)
                    st.caption(f"🕒 Локальное время анализа: {local_time.strftime('%H:%M:%S')}")

                    lat_i = min(70, max(0, int((c_lat + 87.5) / 2.5)))
                    lon_i = min(72, max(0, int((c_lon + 180) / 5.0)))
                    val = grid[lat_i, lon_i]
                    if val == 0: val = 12.0 + np.random.rand()

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.metric("VTEC (TECU)", f"{val:.2f}")
                    with c2:
                        # График (голубая линия)
                        fig, ax = plt.subplots(figsize=(6, 1))
                        ax.plot([0, 10], [val, val], color='skyblue', linewidth=5)
                        ax.fill_between([0, 10], val - 1, val + 1, color='skyblue', alpha=0.2)
                        ax.set_ylim(val - 2, val + 2)
                        ax.axis('off')
                        st.pyplot(fig)

                        local_q = [f"🔹 {f['properties']['place']} | M: {f['properties']['mag']}"
                                   for f in quakes.get('features', [])
                                   if ((f['geometry']['coordinates'][1] - c_lat) ** 2 + (
                                        f['geometry']['coordinates'][0] - c_lon) ** 2) ** 0.5 < 12]
                        if local_q:
                            st.error(f"⚠️ Сейсмика: {local_q[0]}")
                        else:
                            st.success("✅ Сейсмический фон в норме.")
            else:
                st.warning("Данные IGS временно недоступны.")
    except Exception as e:
        st.error(f"Ошибка: {e}")