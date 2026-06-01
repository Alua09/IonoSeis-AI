import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import requests
import gzip
import shutil
import os
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
    """Безопасный парсинг данных IONEX"""
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
                numeric_vals = [float(p) for p in parts if
                                p.replace('.', '').replace('-', '').isdigit() and '-' not in p[1:]]
                if len(numeric_vals) >= 10:
                    for lon_idx, val in enumerate(numeric_vals):
                        if lon_idx < 73 and lat_idx < 71: grid[lat_idx, lon_idx] = val / 10.0
                    lat_idx += 1
    return grid


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный литосферно-ионосферный мониторинг")

if st.button("🔄 ЗАПУСК ЭКСПЕРТНОГО АНАЛИЗА"):
    # Принудительная очистка старых данных перед запуском
    if os.path.exists("data.ionex"): os.remove("data.ionex")
    if os.path.exists("./tmp"): shutil.rmtree("./tmp")

    try:
        with st.spinner("Синхронизация с NASA / NOAA / USGS..."):
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
                kp = get_kp_index()
                quakes = requests.get(
                    f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={(datetime.now() - timedelta(days=1)).isoformat()}").json()

                # Геомагнитный статус
                st.subheader(f"🌐 Геомагнитная обстановка: Kp-индекс {kp}")
                if kp > 4:
                    st.warning("⚠️ Внимание: Геомагнитная активность. Показатели VTEC могут быть завышены.")
                else:
                    st.success("✅ Геомагнитный фон спокоен.")

                # Анализ по городам
                for city, (c_lat, c_lon) in CITIES.items():
                    st.markdown("---")
                    st.subheader(f"📍 Станция: {city}")

                    # Индивидуальное время
                    offset = 6 if city in ["Алматы", "Бишкек"] else 9
                    st.caption(f"🕒 Местное время: {(datetime.utcnow() + timedelta(hours=offset)).strftime('%H:%M:%S')}")

                    lat_i, lon_i = int((c_lat + 87.5) / 2.5), int((c_lon + 180) / 5.0)
                    val = grid[lat_i, lon_i] if grid[lat_i, lon_i] != 0 else 12.0

                    c1, c2 = st.columns([1, 2])
                    c1.metric("VTEC (TECU)", f"{val:.2f}")
                    with c2:
                        fig, ax = plt.subplots(figsize=(5, 0.5))
                        ax.plot([0, 10], [val, val], color='skyblue', linewidth=6)
                        ax.set_ylim(val - 2, val + 2)
                        ax.axis('off')
                        st.pyplot(fig)

                    local_q = [f"🔹 {f['properties']['place']} | M: {f['properties']['mag']}"
                               for f in quakes.get('features', [])
                               if ((f['geometry']['coordinates'][1] - c_lat) ** 2 + (
                                    f['geometry']['coordinates'][0] - c_lon) ** 2) ** 0.5 < 12]

                    if local_q:
                        st.error("⚠️ Сейсмическая активность в радиусе 1200 км:")
                        for q in local_q[:2]: st.write(q)
                    else:
                        st.success("✅ Сейсмический фон в норме.")
            else:
                st.warning("Серверы IGS временно недоступны. Используйте кнопку повторно через 1 минуту.")
    except Exception as e:
        st.error(f"Системная ошибка: {e}")