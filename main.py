import streamlit as st
import earthaccess
import numpy as np
import requests
import gzip
import shutil
import os
from datetime import datetime, timedelta


# ... (функции parse_ionex_data, get_interp_tec и т.д. остаются без изменений) ...

def get_kp_index():
    """Получение актуального Kp-индекса с сайта NOAA"""
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
        data = requests.get(url).json()
        # Берем последнее значение из массива
        return float(data[-1][1])
    except:
        return 2.0  # Среднее значение по умолчанию


# В блоке запуска анализа:
if st.button("🔄 ЗАПУСК ЭКСПЕРТНОГО АНАЛИЗА"):
    # ... (код скачивания и парсинга IONEX) ...

    kp = get_kp_index()
    st.subheader(f"🌐 Геомагнитная обстановка: Kp-индекс {kp}")

    if kp > 4:
        st.warning(
            "⚠️ Внимание: Геомагнитная буря! Высокие показатели VTEC могут быть вызваны солнечной активностью, а не сейсмикой.")
    else:
        st.success("✅ Геомагнитный фон спокоен. Локальные аномалии VTEC могут указывать на литосферные процессы.")

    for city, (c_lat, c_lon) in CITIES.items():
        # ... (ваш цикл вывода данных по городам) ...
        # Добавляем экспертную проверку внутри цикла:
        val = get_interp_tec(grid, c_lat, c_lon)
        if kp <= 4 and val > 25:
            st.error(
                f"🚨 АНОМАЛИЯ: Повышенный VTEC при низком Kp-индексе! Возможен предвестник сейсмического события в зоне {city}.")