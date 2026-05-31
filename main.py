import streamlit as st
import xarray as xr
import gzip
import shutil
import matplotlib.pyplot as plt
import numpy as np

# Используем специализированную библиотеку или парсинг
# Для IONEX 1.0 идеально подходит xarray, если правильно указать параметры
# Но так как файл текстовый, мы будем использовать метод 'ionex' через georinex,
# но теперь мы знаем, что это корректный файл.

if st.button("🚀 Построить карту VTEC"):
    try:
        # У нас уже есть файл 'data.ionex', который мы распаковали ранее
        final_path = "data.ionex"

        # IONEX файлы читаются через библиотеку georinex,
        # нужно просто передать аргумент 'use'
        import georinex as gr

        ds = gr.load(final_path)

        st.success("Данные считаны успешно!")

        # Визуализация TEC
        fig, ax = plt.subplots(figsize=(10, 6))
        # В этом файле переменная называется 'TEC'
        ds['TEC'].isel(time=0).plot(ax=ax)
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Ошибка при чтении: {e}")
        st.write("Попробуйте убедиться, что georinex установлен: pip install georinex")