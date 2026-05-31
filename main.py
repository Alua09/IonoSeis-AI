import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import gzip
import shutil
import os


def parse_upc_ionex(file_path):
    # Распаковываем .gz
    with gzip.open(file_path, 'rb') as f_in:
        with open("data.ionex", 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    tec_values = []
    # Читаем распакованный файл
    with open("data.ionex", 'r', errors='ignore') as f:
        in_block = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_block = True
            elif 'END OF TEC MAP' in line:
                in_block = False
            elif in_block and not any(x in line for x in ['LAT/LON1/LON2', 'EPOCH']):
                # В этом формате данные идут в одну строку, разделенные пробелами
                parts = line.split()
                for p in parts:
                    try:
                        val = float(p)
                        if val < 9000: tec_values.append(val)
                    except:
                        continue

    # Для UPC карт сетка обычно 71x73
    data = np.array(tec_values)
    return data[:5183].reshape((71, 73))


# --- ВСТАВЬТЕ ЭТО В ВАШУ КНОПКУ ---
if st.button("🚀 ПОСТРОИТЬ КАРТУ ИЗ UPC"):
    try:
        # Указываем имя скачанного файла
        grid = parse_upc_ionex("./tmp/UPC0OPSFIN_20261210000_01D_02H_GIM.INX.gz")

        fig, ax = plt.subplots(figsize=(10, 5))
        # Визуализация
        im = ax.imshow(np.flipud(grid.T), cmap='jet', interpolation='bicubic',
                       extent=[-180, 180, -87.5, 87.5], aspect='auto')

        plt.colorbar(im, label='VTEC')
        ax.set_title("Глобальная карта VTEC (UPC Analysis Center)")
        st.pyplot(fig)

        st.success("Данные успешно визуализированы!")
    except Exception as e:
        st.error(f"Ошибка при парсинге: {e}")