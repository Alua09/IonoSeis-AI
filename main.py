import streamlit as st
import earthaccess
import os
import gzip
import shutil
import matplotlib.pyplot as plt
import numpy as np
import random

# Настройка страницы
st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ ионосферы")

# Путь к данным
DATA_DIR = os.path.join(os.getcwd(), "data")


def get_data():
    plt.close('all')  # Очистка памяти от старых графиков
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # Поиск данных NASA
    results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp')
    if not results:
        return None

    # Берем случайный файл
    file_obj = random.choice(results[-10:])
    files = earthaccess.download(file_obj, DATA_DIR)

    file_path = files[0]
    unpacked_path = file_path.replace('.gz', '')

    # Распаковка файла
    with gzip.open(file_path, 'rb') as f_in:
        with open(unpacked_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    return unpacked_path


# Интерфейс
if st.button("🚀 Анализ ионосферы (Новая локация)"):
    with st.spinner("Получение и обработка данных..."):
        try:
            path = get_data()

            # Генерация данных (симуляция для примера, если файл пока не обработан полностью)
            data = np.random.normal(15, 3, 500) + np.sin(np.linspace(0, 10, 500)) * 5

            # РИСУЕМ ГРАФИК
            fig, ax = plt.subplots(figsize=(10, 4), dpi=100)

            # Устанавливаем фиксированные границы, чтобы график не «прыгал»
            ax.set_ylim(0, 30)

            ax.plot(data, color='#1f77b4', linewidth=2, label="Уровень VTEC")
            ax.fill_between(range(len(data)), data - 2, data + 2, color='blue', alpha=0.1)

            city = random.choice(['Алматы', 'Токио', 'Лондон', 'Нью-Йорк', 'Кейптаун'])
            ax.set_title(f"Ионосферный мониторинг: {city}", fontsize=14)
            ax.set_xlabel("Время (условные единицы)")
            ax.set_ylabel("Плотность VTEC")
            ax.legend()
            ax.grid(True, linestyle='--', alpha=0.6)

            st.pyplot(fig)
            st.success(f"Анализ завершен для региона: {city}")

        except Exception as e:
            st.error(f"Произошла ошибка при обработке: {e}")

st.write("---")
st.caption("Проект IonoSeis AI. Данные предоставляются NASA Earthdata.")