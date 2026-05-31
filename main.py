import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import gzip
import shutil

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ IONEX")

if st.button("🚀 Обработать файл вручную"):
    try:
        final_path = "data.ionex"

        # Для файлов IONEX формата 1.0 от NRCAN лучше всего подходит
        # использование xarray для чтения напрямую, если он поддерживает этот формат.
        # Если нет, мы используем встроенные средства.

        st.write("Попытка чтения файла...")

        # Пытаемся открыть данные.
        # Если файл стандартный IONEX, xarray считывает его как данные.
        ds = xr.open_dataset(final_path, engine='netcdf4')

        st.success("Данные успешно считаны!")

        fig, ax = plt.subplots(figsize=(10, 6))
        ds['TEC'].isel(time=0).plot(ax=ax)
        st.pyplot(fig)

    except Exception as e:
        # Если xarray не может открыть, значит он видит файл как текст.
        # В этом случае мы выводим сообщение о том, что нужно использовать
        # специфический парсер для IONEX.
        st.error(f"Ошибка парсинга: {e}")
        st.info("Поскольку georinex и xarray не могут прочитать этот текстовый файл, "
                "нам нужно использовать библиотеку 'ionex' или 'pygna'.")
        st.write("Попробуйте выполнить: pip install ionex")