import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import patoolib
import os
from datetime import datetime

st.set_page_config(layout="wide")
st.title("🛰 IonoSeis AI: Полная обработка данных")

# Данные авторизации
USER = st.secrets["EARTHDATA_USERNAME"]
PASSWORD = st.secrets["EARTHDATA_PASSWORD"]


def process_data():
    day = datetime.now().strftime("%j")
    year = datetime.now().strftime("%y")
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/2026/{day}/igsg{day}0.{year}i.Z"

    # 1. Скачивание
    response = requests.get(url, auth=(USER, PASSWORD))
    with open("data.Z", "wb") as f:
        f.write(response.content)

    # 2. Распаковка
    patoolib.extract_archive("data.Z", outdir=".", verbosity=-1)
    # После распаковки файл будет называться igsg...i
    extracted_file = f"igsg{day}0.{year}i"

    # 3. Парсинг
    tec_values = []
    with open(extracted_file, 'r', errors='ignore') as f:
        in_block = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_block = True
            elif 'END OF TEC MAP' in line:
                in_block = False
            elif in_block and any(c.isdigit() for c in line.split()):
                for p in line.split():
                    try:
                        val = float(p)
                        if val < 9000: tec_values.append(val)
                    except:
                        continue
    return np.array(tec_values).reshape((71, 73))


if st.button("🚀 ПОСТРОИТЬ КАРТУ"):
    try:
        grid = process_data()

        fig, ax = plt.subplots(figsize=(10, 5))
        im = ax.imshow(np.flipud(grid.T), cmap='jet', interpolation='bicubic',
                       extent=[-180, 180, -87.5, 87.5], aspect='auto')

        plt.colorbar(im, label='VTEC')
        ax.set_title("Актуальная карта VTEC")
        st.pyplot(fig)

        st.success("Данные успешно обработаны.")
    except Exception as e:
        st.error(f"Ошибка при парсинге: {e}")