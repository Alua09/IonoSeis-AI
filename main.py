import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime

st.set_page_config(layout="wide", page_title="IonoSeis AI: Полная система")
st.title("🛰 IonoSeis AI: Анализ ионосферы")

# --- НАСТРОЙКИ ---
USER = st.secrets.get("EARTHDATA_USERNAME", "")
PASSWORD = st.secrets.get("EARTHDATA_PASSWORD", "")


def fetch_ionex_data():
    """Скачивает и возвращает путь к файлу"""
    # Ссылка на архив NASA CDDIS (данные IGS)
    date_path = datetime.now().strftime("%Y/%j")
    filename = f"igsg{datetime.now().strftime('%j')}0.{datetime.now().strftime('%y')}i"
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/{date_path}/{filename}.Z"

    response = requests.get(url, auth=(USER, PASSWORD), stream=True)
    if response.status_code == 200:
        path = "data.ionex"
        with open(path, 'wb') as f:
            f.write(response.content)
        return path
    return None


def parse_ionex(file_path):
    """Парсинг формата IONEX"""
    tec_values = []
    with open(file_path, 'r', errors='ignore') as f:
        in_block = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_block = True
            elif 'END OF TEC MAP' in line:
                in_block = False
            elif in_block and any(c.isdigit() for c in line):
                parts = line.split()
                for p in parts:
                    try:
                        val = float(p)
                        if val < 9000: tec_values.append(val)
                    except:
                        continue
    # Возвращаем массив 71x73
    data = np.array(tec_values)
    return data[:5183].reshape((71, 73))


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ЗАПУСК ПОЛНОГО ЦИКЛА"):
    try:
        with st.spinner("Загрузка с серверов NASA..."):
            file_path = fetch_ionex_data()
            if not file_path:
                st.error("Ошибка скачивания. Сервер NASA может быть недоступен.")
                st.stop()

            grid = parse_ionex(file_path)

            # Визуализация
            fig, ax = plt.subplots(figsize=(10, 5))
            im = ax.imshow(np.flipud(grid.T), cmap='jet', interpolation='bicubic',
                           aspect='auto', extent=[-180, 180, -87.5, 87.5])

            plt.colorbar(im, label='VTEC')
            ax.set_title("Глобальная карта VTEC")
            st.pyplot(fig)

            # Статистика
            st.write(f"Средний уровень VTEC: {np.mean(grid):.2f}")
            st.success("Анализ завершен.")

    except Exception as e:
        st.error(f"Критическая ошибка: {e}")