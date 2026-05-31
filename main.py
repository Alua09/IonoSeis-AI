import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import gzip
import shutil
import os
import re
from datetime import datetime, timedelta

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis AI: Полный мониторинг")
st.title("🛰 IonoSeis AI: Гармоники ионосферы")


# --- УНИВЕРСАЛЬНЫЙ ПАРСЕР ---
def parse_ionex_any_file(file_path):
    path_str = str(file_path)
    # Распаковка если это архив
    if path_str.endswith('.gz'):
        with gzip.open(path_str, 'rb') as f_in:
            with open("temp_data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
        target = "temp_data.ionex"
    else:
        target = path_str

    with open(target, 'r', errors='ignore') as f:
        content = f.read()

    # Извлекаем все числа из файла (устойчиво к изменению структуры IONEX)
    # Ищем последовательности, похожие на значения VTEC
    all_floats = [float(x) for x in re.findall(r'-?\d+\.\d+', content)]
    data = np.array(all_floats)

    # Проверка на наличие данных (минимум 5000 точек для сетки 71x73)
    if data.size < 5000:
        raise ValueError(f"Не удалось извлечь достаточно данных. Найдено: {data.size}")

    return data[:5183].reshape((71, 73))


# --- ПОЛУЧЕНИЕ ЗНАЧЕНИЯ ДЛЯ ТОЧКИ ---
def get_vtec(grid, lat, lon):
    lat_idx = int((lat + 87.5) / 2.5)
    lon_idx = int((lon + 180) / 5.0)
    return grid[min(lat_idx, 70), min(lon_idx, 72)]


# --- ОСНОВНАЯ ЛОГИКА ---
if st.button("🚀 ЗАПУСК: ПОЛНЫЙ ЦИКЛ АНАЛИЗА"):
    try:
        with st.spinner("Связь с сервером NASA и обработка..."):
            # Авторизация
            earthaccess.login(strategy="netrc")

            # Поиск
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now() - timedelta(days=7), datetime.now()),
                count=7
            )

            if not results:
                st.error("Данные не найдены за последние 7 дней.")
                st.stop()

            # Скачивание
            paths = earthaccess.download(results, ".")

            almaty_series, tokyo_series = [], []
            for f in paths:
                try:
                    grid = parse_ionex_any_file(f)
                    almaty_series.append(get_vtec(grid, 43.2, 76.9))
                    tokyo_series.append(get_vtec(grid, 35.6, 139.6))
                except Exception as inner_e:
                    st.warning(f"Пропуск файла {os.path.basename(str(f))}: {inner_e}")

            # Построение графиков
            if almaty_series:
                fig, ax = plt.subplots(figsize=(12, 5))
                ax.plot(almaty_series, label='Алматы (43.2°N, 76.9°E)', marker='o', color='green', linewidth=2)
                ax.plot(tokyo_series, label='Токио (35.6°N, 139.6°E)', marker='s', color='blue', linewidth=2)
                ax.set_title("Гармонический пульс ионосферы (Временной ряд)")
                ax.set_xlabel("Срез данных (по времени)")
                ax.set_ylabel("VTEC Units")
                ax.legend()
                ax.grid(True, alpha=0.6)
                st.pyplot(fig)
                st.success("Графики успешно построены.")
            else:
                st.error("Не удалось построить график: недостаточно данных после парсинга.")

    except Exception as e:
        st.error(f"Критическая ошибка: {e}")