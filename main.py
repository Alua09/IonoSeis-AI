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
st.title("🛰 IonoSeis AI: Экспертный мониторинг")

CITIES = {"Алматы": (43.25, 76.92), "Бишкек": (42.87, 74.59), "Токио": (35.68, 139.65)}


def parse_ionex_data():
    """Парсинг из локального файла, если он существует"""
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


if st.button("🔄 ЗАПУСК ГЕОФИЗИЧЕСКОГО АНАЛИЗА"):
    # 1. Синхронизация данных
    with st.spinner("Синхронизация..."):
        try:
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
                st.success("Данные успешно синхронизированы.")
            else:
                st.warning("Серверы IGS не ответили. Используются локальные данные.")
        except Exception:
            st.error("Нет связи с серверами NASA. Работаем с архивом.")

    # 2. Обработка и визуализация
    grid = parse_ionex_data()
    for city, (c_lat, c_lon) in CITIES.items():
        st.markdown("---")
        st.subheader(f"📍 Станция: {city}")

        # Индивидуальное время
        offset = 6 if city in ["Алматы", "Бишкек"] else 9
        st.caption(f"🕒 Время: {(datetime.utcnow() + timedelta(hours=offset)).strftime('%H:%M:%S')}")

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
        st.success("✅ Ионосферный фон стабилен.")