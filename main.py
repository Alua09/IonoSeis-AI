import streamlit as st
import numpy as np
import gzip
import shutil
import matplotlib.pyplot as plt
import re

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Парсер IONEX")

if st.button("🚀 Обработать и визуализировать"):
    try:
        final_path = "data.ionex"

        # Читаем файл целиком
        with open(final_path, 'r', encoding='ascii', errors='ignore') as f:
            content = f.read()

        # Ищем блок данных TEC между заголовками
        # Используем regex для поиска всех чисел в блоках TEC MAP
        # Обычно сетка имеет размер 73 долготы x 71 широту

        # Находим первый попавшийся блок данных
        match = re.search(r"START OF TEC MAP(.*?)END OF TEC MAP", content, re.DOTALL)

        if match:
            block = match.group(1)
            # Извлекаем все числа из блока
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", block)
            data = np.array([float(n) for n in numbers])

            # В IONEX сетка обычно 71 по широте, 73 по долготе (как указано в заголовке)
            # 71 * 73 = 5183 точки
            if len(data) >= 5183:
                grid = data[:5183].reshape((71, 73))

                fig, ax = plt.subplots(figsize=(8, 6))
                im = ax.imshow(grid, cmap='viridis', origin='lower')
                plt.colorbar(im, label='TEC (0.1 TECU)')
                st.pyplot(fig)
                st.success("Карта VTEC успешно построена!")
            else:
                st.error(f"Данных найдено: {len(data)}, а нужно 5183. Проверьте размерность.")
        else:
            st.error("Не удалось найти блоки 'START OF TEC MAP'. Возможно, файл специфический.")

    except Exception as e:
        st.error(f"Ошибка парсинга: {e}")