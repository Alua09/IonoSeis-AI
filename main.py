import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ VTEC")

# Прямая ссылка на актуальные данные GIM (IGS)
# Используем формат IONEX (или NetCDF, если сервер отдает)
DATA_URL = "https://cddis.nasa.gov/archive/gnss/products/ionex/2026/150/casg1500.26i.Z"

if st.button("🚀 Загрузить данные из актуального каталога"):
    with st.spinner("Загрузка данных..."):
        try:
            # Поскольку файл сжат (.Z), xarray не всегда умеет открывать его напрямую.
            # Мы попробуем загрузить данные через библиотеку netCDF4/xarray
            # Если файл не читается как netCDF, значит это чистый IONEX.

            st.write(f"Попытка доступа к: {DATA_URL}")

            # Для работы с .Z файлами напрямую из кода нужно больше инструментов,
            # поэтому мы используем xarray для чтения напрямую по URL,
            # если сервер поддерживает NetCDF.
            ds = xr.open_dataset(DATA_URL)

            st.success("Данные успешно считаны!")
            fig, ax = plt.subplots(figsize=(10, 6))
            ds['TEC'].isel(time=0).plot(ax=ax)
            st.pyplot(fig)

        except Exception as e:
            st.error(f"Ошибка при прямом чтении: {e}")
            st.info("Попробуйте убедиться, что файл доступен по прямой ссылке.")