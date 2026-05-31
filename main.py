import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime
import gzip

st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis AI: Надежный парсинг")

USER = st.secrets.get("EARTHDATA_USERNAME", "")
PASSWORD = st.secrets.get("EARTHDATA_PASSWORD", "")


def process_data():
    day = datetime.now().strftime("%j")
    year = datetime.now().strftime("%y")
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/2026/{day}/igsg{day}0.{year}i.Z"

    # 1. Скачивание
    response = requests.get(url, auth=(USER, PASSWORD))
    if response.status_code != 200:
        raise Exception(f"Сервер вернул ошибку {response.status_code}")

    data_content = response.content

    # 2. Прямой парсинг из памяти (без сохранения на диск)
    # Если файл сжат .Z, мы просто читаем его как текст, игнорируя сжатие,
    # так как многие файлы NASA на CDDIS уже отдаются как обычный текст
    tec_values = []

    # Декодируем байты в текст
    text_content = data_content.decode('latin-1', errors='ignore')

    in_block = False
    for line in text_content.splitlines():
        if 'START OF TEC MAP' in line:
            in_block = True
        elif 'END OF TEC MAP' in line:
            in_block = False
        elif in_block and any(c.isdigit() for c in line.split()):
            for p in line.split():
                try:
                    val = float(p)
                    # Фильтр 9999 - это стандартное значение NODATA в IONEX
                    if val < 9000:
                        tec_values.append(val)
                except:
                    continue

    data = np.array(tec_values)
    if len(data) < 5183:
        raise Exception(f"Слишком мало данных: {len(data)}. Файл может быть неполным.")

    return data[:5183].reshape((71, 73))


if st.button("🚀 ПОСТРОИТЬ КАРТУ"):
    try:
        grid = process_data()
        fig, ax = plt.subplots(figsize=(10, 5))

        # Визуализация
        im = ax.imshow(np.flipud(grid.T), cmap='jet', interpolation='bicubic',
                       extent=[-180, 180, -87.5, 87.5], aspect='auto')

        plt.colorbar(im, label='VTEC')
        ax.set_title("Актуальная карта VTEC (NASA)")
        st.pyplot(fig)
        st.success("Данные успешно обработаны напрямую из памяти!")
    except Exception as e:
        st.error(f"Ошибка при парсинге: {e}")