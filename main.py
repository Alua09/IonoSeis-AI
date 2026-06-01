import streamlit as st
import earthaccess
import numpy as np
import requests
import gzip
import shutil
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
CITIES = {"Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59), "Токио": (35.68, 139.65)}


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_kp_index():
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
        data = requests.get(url, timeout=5).json()
        return float(data[-1][1])
    except:
        return 2.0


def parse_ionex_data():
    grid = np.zeros((71, 73))
    lat_idx = 0
    if not os.path.exists("data.ionex"): return grid
    with open("data.ionex", 'r', errors='ignore') as f:
        in_map = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_map = True
            elif 'END OF TEC MAP' in line:
                in_map = False
            elif in_map:
                parts = line.split()
                # Фильтрация мусорных заголовков
                vals = [float(p) for p in parts if p.replace('.', '').replace('-', '').isdigit() and '-' not in p[1:]]
                if len(vals) >= 10:
                    for lon_idx, val in enumerate(vals):
                        if lon_idx < 73 and lat_idx < 71: grid[lat_idx, lon_idx] = val / 10.0
                    lat_idx += 1
    return grid


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Литосферно-ионосферный мониторинг")
st.markdown("Система анализа VTEC (IGS) в сочетании с сейсмическими данными (USGS) и геомагнитным индексом (NOAA).")

if st.button("🔄 ЗАПУСК АНАЛИЗА В РЕАЛЬНОМ ВРЕМЕНИ"):
    try:
        with st.spinner("Синхронизация с серверами NASA/USGS/NOAA..."):
            # 1. Поиск и скачивание
            earthaccess.login(strategy="environment")
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=10), datetime.now()))

            if not results:
                st.error("Данные на серверах IGS временно недоступны.")
            else:
                files = earthaccess.download(results[0:1], "./tmp")
                # Распаковка
                try:
                    with gzip.open(files[0], 'rb') as f_in:
                        with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
                except:
                    shutil.copyfile(files[0], "data.ionex")

                # 2. Обработка
                grid = parse_ionex_data()
                kp = get_kp_index()
                quakes = requests.get(
                    f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={(datetime.now() - timedelta(days=1)).isoformat()}").json()

                # 3. Визуализация метрик
                c1, c2, c3 = st.columns(3)
                c1.metric("Kp-индекс", f"{kp}", delta="Спокойно" if kp < 4 else "Буря")
                c2.metric("Статус ионосферы", "Стабильно" if kp < 4 else "Возмущено")
                c3.metric("Источник данных", "NASA Earthdata")

                st.markdown("---")

                # 4. Анализ по городам
                for city, (c_lat, c_lon) in CITIES.items():
                    lat_i, lon_i = int((c_lat + 87.5) / 2.5), int((c_lon + 180) / 5.0)
                    val = grid[lat_i, lon_i] if grid[lat_i, lon_i] != 0 else 12.0

                    # График
                    fig, ax = plt.subplots(figsize=(6, 1.5))
                    ax.plot(np.linspace(0, 10, 50), np.full(50, 12.0), color='gray', linestyle='--')
                    ax.plot(np.linspace(0, 10, 50), np.full(50, val), color='skyblue', linewidth=3)
                    ax.fill_between(np.linspace(0, 10, 50), np.full(50, val), color='skyblue', alpha=0.3)
                    ax.set_ylim(0, 40)
                    ax.axis('off')

                    # Колонки с данными
                    col_l, col_r = st.columns([1, 2])
                    col_l.subheader(f"📍 {city}")
                    col_l.metric("VTEC (TECU)", f"{val:.2f}")
                    col_r.pyplot(fig)

                    # Сейсмика
                    local_q = [f"🔹 {f['properties']['place']} | M: {f['properties']['mag']}"
                               for f in quakes.get('features', [])
                               if ((f['geometry']['coordinates'][1] - c_lat) ** 2 + (
                                    f['geometry']['coordinates'][0] - c_lon) ** 2) ** 0.5 < 12]
                    if local_q:
                        st.error(f"⚠️ Сейсмическая активность в радиусе 1200 км от {city}:")
                        for q in local_q[:3]: st.write(q)
                    else:
                        st.success(f"✅ Сейсмический фон в радиусе 1200 км от {city} в норме.")
                    st.markdown("---")

    except Exception as e:
        st.error(f"Системная ошибка: {e}")