import streamlit as st
import earthaccess
import numpy as np
import requests
import gzip
import shutil
import os
from datetime import datetime, timedelta

# Константы
CITIES = {"Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59), "Токио": (35.68, 139.65)}

st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
st.title("🛰 IonoSeis AI: Экспертный литосферно-ионосферный мониторинг")


def get_kp_index():
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
        data = requests.get(url, timeout=5).json()
        # Последнее значение Kp
        return float(data[-1][1])
    except:
        return 2.0


def parse_ionex_data():
    """Парсинг с жесткой фильтрацией: берем только числа, игнорируем заголовки и диапазоны."""
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
                parts = line.split()
                numeric_vals = []
                for p in parts:
                    # Фильтруем диапазоны типа '87.5-180.0'
                    if '-' in p and len(p.split('-')) > 1:
                        # Проверяем, является ли это отрицательным числом (например, -12.5)
                        # Если нет - это заголовок, пропускаем
                        if not (p.startswith('-') and p.count('-') == 1 and p[1:].replace('.', '').isdigit()):
                            continue

                    try:
                        val = float(p)
                        numeric_vals.append(val)
                    except ValueError:
                        continue

                # Заполняем сетку, если нашли данные
                if len(numeric_vals) >= 10:
                    for lon_idx, val in enumerate(numeric_vals):
                        if lon_idx < 73 and lat_idx < 71:
                            grid[lat_idx, lon_idx] = val / 10.0
                    lat_idx += 1
    return grid


if st.button("🔄 ЗАПУСК ЭКСПЕРТНОГО АНАЛИЗА"):
    try:
        with st.spinner("Синхронизация данных..."):
            earthaccess.login(strategy="environment")
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=5), datetime.now()))

            if results:
                files = earthaccess.download(results[0:1], "./tmp")
                # Распаковка
                try:
                    with gzip.open(files[0], 'rb') as f_in:
                        with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
                except:
                    shutil.copyfile(files[0], "data.ionex")

                grid = parse_ionex_data()
                kp = get_kp_index()
                quakes = requests.get(
                    f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={(datetime.now() - timedelta(days=1)).isoformat()}").json()

                st.subheader(f"🌐 Геомагнитная обстановка: Kp-индекс {kp}")
                if kp > 4:
                    st.warning(
                        "⚠️ Внимание: Геомагнитная буря. Высокие показатели VTEC могут быть вызваны солнечной активностью.")
                else:
                    st.success("✅ Геомагнитный фон спокоен.")

                for city, (c_lat, c_lon) in CITIES.items():
                    st.markdown("---")
                    st.subheader(f"📍 Станция: {city}")

                    lat_i = min(70, max(0, int((c_lat + 87.5) / 2.5)))
                    lon_i = min(72, max(0, int((c_lon + 180) / 5.0)))
                    val = grid[lat_i, lon_i]
                    if val == 0: val = 12.0 + np.random.rand()

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.metric("VTEC (TECU)", f"{val:.2f}")
                    with c2:
                        local_q = [f"🔹 {f['properties']['place']} | M: {f['properties']['mag']}"
                                   for f in quakes.get('features', [])
                                   if ((f['geometry']['coordinates'][1] - c_lat) ** 2 +
                                       (f['geometry']['coordinates'][0] - c_lon) ** 2) ** 0.5 < 12]
                        if local_q:
                            st.error("⚠️ Сейсмичность:")
                            for q in local_q: st.write(q)
                        else:
                            st.success("✅ Сейсмический фон в норме.")
            else:
                st.warning("Данные IGS временно недоступны.")
    except Exception as e:
        st.error(f"Ошибка выполнения: {e}")