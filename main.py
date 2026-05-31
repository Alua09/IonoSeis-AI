import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import re

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Итоговая карта VTEC")

if st.button("🚀 Построить корректную карту"):
    try:
        final_path = "data.ionex"
        with open(final_path, 'r', encoding='ascii', errors='ignore') as f:
            content = f.read()

        # Ищем блок данных TEC
        match = re.search(r"START OF TEC MAP(.*?)END OF TEC MAP", content, re.DOTALL)

        if match:
            block = match.group(1)
            # Извлекаем все числа (включая отрицательные)
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", block)
            data = np.array([float(n) for n in numbers])

            # 1. Фильтруем "9999" и другие аномальные значения
            data[data >= 9000] = np.nan

            # 2. Формируем сетку (71 широта, 73 долгота)
            # Если карта все еще «полосатая», мы делаем транспонирование .T
            if len(data) >= 5183:
                grid = data[:5183].reshape((71, 73)).T

                fig, ax = plt.subplots(figsize=(10, 5))

                # Используем origin='lower' для правильной ориентации по широте
                im = ax.imshow(grid, cmap='plasma', origin='lower', aspect='auto',
                               extent=[-180, 180, -87.5, 87.5])

                plt.colorbar(im, label='VTEC (0.1 TECU)')
                ax.set_xlabel("Долгота")
                ax.set_ylabel("Широта")
                ax.set_title("Глобальная карта ионосферы (GIM)")

                st.pyplot(fig)
                st.success("Карта успешно построена!")
            else:
                st.error("Недостаточно данных для построения сетки.")
        else:
            st.error("Не удалось найти блок данных TEC.")

    except Exception as e:
        st.error(f"Ошибка: {e}")