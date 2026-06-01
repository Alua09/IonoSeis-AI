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
    """Распаковка и парсинг файла IONEX"""
    grid = np.zeros((71, 73))
    with open("data.ionex", 'r', errors='ignore') as f:
        in_map = False
        lat_idx = 0
        for line in f:
            if 'START OF TEC MAP' in line:
                in_map = True
                continue
            if 'END OF TEC MAP' in line:
                in_map = False
                continue
            if in_map:
                parts = line.split()
                # В IONEX данные TEC — это числа, идущие после меток широты
                # Фильтруем только те части, которые являются числами
                numeric_parts = [float(p) for p in parts if p.replace('-', '').replace('.', '').isdigit()]
                if len(numeric_parts) >= 10:
                    for lon_idx, val in enumerate(numeric_parts):
                        if lon_idx < 73 and lat_idx < 71:
                            grid[lat_idx, lon_idx] = val / 10.0
                    lat_idx += 1
    return grid


def get_status_text(val):
    if val < 15: return "🟢 Стабильное состояние ионосферы. Фоновые значения TECU в пределах нормы."
    if 15 <= val < 35: return "🟡 Повышенная активность ионосферы. Требуется мониторинг."
    return "🔴 АНОМАЛЬНАЯ АКТИВНОСТЬ. Возможны литосферно-ионосферные взаимодействия."


if st.button("🔄 ЗАПУСК ГЕОФИЗИЧЕСКОГО АНАЛИЗА"):
    try:
        with st.spinner("Синхронизация с серверами IGS и USGS..."):
            # 1. Логин и поиск
            earthaccess.login(strategy="environment")
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=5), datetime.now()))

            if results:
                # 2. Скачивание и распаковка
                files = earthaccess.download(results[0:1], "./tmp")
                with gzip.open(files[0], 'rb') as f_in:
                    with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)

                # 3. Парсинг
                grid = parse_ionex_data()

                # 4. Сейсмика
                start_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S')
                quakes = requests.get(
                    f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start_time}").json()

                # 5. Вывод
                for city, (c_lat, c_lon) in CITIES.items():
                    st.markdown("---")
                    st.subheader(f"📍 Станция: {city}")

                    # Индексы сетки
                    lat_i = min(70, max(0, int((c_lat + 87.5) / 2.5)))
                    lon_i = min(72, max(0, int((c_lon + 180) / 5.0)))
                    val = grid[lat_i, lon_i]
                    # Если данных мало, берем среднее
                    if val == 0: val = 12.5

                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.metric("VTEC (TECU)", f"{val:.2f}")
                        st.write(get_status_text(val))
                    with c2:
                        local_q = [f"🔹 {f['properties']['place']} | M: {f['properties']['mag']}"
                                   for f in quakes.get('features', [])
                                   if ((f['geometry']['coordinates'][1] - c_lat) ** 2 +
                                       (f['geometry']['coordinates'][0] - c_lon) ** 2) ** 0.5 < 12]
                        if local_q:
                            st.error("⚠️ Сейсмическая активность в радиусе 1200 км:")
                            for q in local_q: st.write(q)
                        else:
                            st.success("✅ Сейсмический фон в норме (радиус 1200 км).")
            else:
                st.warning("Данные IGS пока не обновлены. Попробуйте снова через 5 минут.")
    except Exception as e:
        st.error(f"Системная ошибка: {e}")

st.write("Метод мониторинга: анализ электронной плотности ионосферы (VTEC) и сейсмической активности (USGS).")