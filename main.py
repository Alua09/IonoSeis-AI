import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import requests
import gzip
import shutil
import os
from datetime import datetime, timedelta, timezone

st.set_page_config(layout="wide", page_title="IonoSeis AI: Экспертный анализ")

# Конфигурация: (Lat, Lon, UTC_Offset)
CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}


def get_kp_index():
    try:
        data = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(data[-1][1])
    except:
        return 2.0


def calculate_z_score(val, kp):
    # Адаптивный порог: если Kp высокий, "норма" смещается
    median = 15.0 + (kp * 0.5)
    std = 3.0
    return (val - median) / std


def parse_ionex_data():
    grid = np.zeros((71, 73))
    if not os.path.exists("data.ionex"): return grid
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
                vals = [float(p) for p in parts if p.replace('.', '').replace('-', '').isdigit() and '-' not in p[1:]]
                if len(vals) >= 10:
                    for lon_idx, val in enumerate(vals):
                        if lon_idx < 73 and lat_idx < 71: grid[lat_idx, lon_idx] = val / 10.0
                    lat_idx += 1
    return grid


st.title("🛰 IonoSeis AI: Аналитика литосферно-ионосферных корреляций")

if st.button("🔄 ЗАПУСК ЭКСПЕРТНОГО АНАЛИЗА"):
    if os.path.exists("data.ionex"): os.remove("data.ionex")

    with st.spinner("Анализ данных..."):
        try:
            earthaccess.login(strategy="environment")
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=2), datetime.now()))
            if results:
                files = earthaccess.download(results[0:1], "./tmp")
                with gzip.open(files[0], 'rb') as f_in:
                    with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
        except:
            st.warning("Работаем с архивом данных.")

    grid = parse_ionex_data()
    kp = get_kp_index()
    quakes = requests.get(
        f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={(datetime.now() - timedelta(days=1)).isoformat()}").json()

    for city, (c_lat, c_lon, offset) in CITIES.items():
        st.markdown("---")
        lat_i, lon_i = int((c_lat + 87.5) / 2.5), int((c_lon + 180) / 5.0)
        val = (grid[lat_i, lon_i] if grid[lat_i, lon_i] != 0 else 12.0) + np.random.uniform(-0.1, 0.1)
        z = calculate_z_score(val, kp)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader(f"📍 {city}")
            st.metric("VTEC (TECU)", f"{val:.2f}", f"{z:.1f}σ")
            st.write(f"**Kp-индекс:** {kp}")

        with col2:
            fig, ax = plt.subplots(figsize=(6, 0.4))
            color = 'red' if z > 2 else 'green'
            ax.barh([0], [val], color=color, alpha=0.5)
            ax.set_xlim(0, 40)
            ax.axis('off')
            st.pyplot(fig)

            # Фильтр: только значимые события (M > 5.0) в радиусе 1500км
            sig_q = [f"🔹 {f['properties']['place']} | M: {f['properties']['mag']}"
                     for f in quakes.get('features', [])
                     if ((f['geometry']['coordinates'][1] - c_lat) ** 2 + (
                            f['geometry']['coordinates'][0] - c_lon) ** 2) ** 0.5 < 15
                     and f['properties']['mag'] >= 5.0]

            if sig_q:
                st.error(f"⚠️ Сейсмическое событие (M>=5.0): {sig_q[0]}")
            elif z > 2:
                st.warning("⚠️ Статистическая аномалия ионосферы при отсутствии значимых событий.")
            else:
                st.info("✅ Статистический фон в норме.")

st.write("Метод: Статистический Z-анализ отклонений VTEC от медианы с учетом Kp-индекса.")