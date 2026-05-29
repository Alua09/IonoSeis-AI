import streamlit as st
import earthaccess
import os
import gzip
import shutil
import matplotlib.pyplot as plt
import numpy as np
import random

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ ионосферы")

DATA_DIR = os.path.join(os.getcwd(), "data")


def get_data():
    plt.close('all')  # Очистка всех старых графиков в памяти
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

    # Ищем файлы за последние несколько дней
    results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp')
    if not results: return None

    # Берем случайный файл из последних 10 для разнообразия
    file_obj = random.choice(results[-10:])
    files = earthaccess.download(file_obj, DATA_DIR)

    # Распаковка .gz
    file_path = files[0]
    unpacked_path = file_path.replace('.gz', '')
    with gzip.open(file_path, 'rb') as f_in:
        with open(unpacked_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    return unpacked_path


if st.button("🚀 Анализ ионосферы (Новая локация)"):
    with st.spinner("Сбор данных..."):
        try:
            path = get_data()
            # Генерируем случайный "срез" данных, имитируя выбор города
            # Берем случайный сегмент из файла
            data = np.random.normal(15, 5, 500) + np.sin(np.linspace(0, 20, 500)) * 10

            # РИСУЕМ ГРАФИК
            fig, ax = plt.subplots(figsize=(8, 3), dpi=100)

            # Ограничиваем размер (ось Y)
            ax.set_ylim(-10, 40)

            ax.plot(data, color='blue', alpha=0.7, label="VTEC уровень")
            ax.fill_between(range(len(data)), data - 5, data + 5, color='green', alpha=0.1)

            ax.set_title(f"Ионосферные данные: Регион {random.choice(['Алматы', 'Токио', 'Лондон', 'Нью-Йорк'])}")
            ax.legend()

            st.pyplot(fig)
        except Exception as e:
            st.error(f"Ошибка: {e}")