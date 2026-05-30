import streamlit as st
import os
import glob
import xarray as xr
import matplotlib.pyplot as plt

st.set_page_config(page_title="IonoSeis AI: Real Data", layout="wide")
st.title("🛰 Анализ реальных ионосферных данных")

DATA_DIR = "data"


def load_real_data():
    # Ищем файлы в папке data (например, .nc или .ionex)
    files = glob.glob(os.path.join(DATA_DIR, "*.nc"))  # Или ваш формат
    if not files:
        return None
    # Загружаем последний файл
    ds = xr.open_dataset(files[-1])
    return ds


if st.button("📊 Построить график по реальным данным"):
    ds = load_real_data()
    if ds is not None:
        st.success("Данные успешно загружены!")

        # Строим график по первой доступной переменной (например, TEC)
        var_name = list(ds.data_vars)[0]
        fig, ax = plt.subplots(figsize=(10, 5))
        ds[var_name].isel(time=0).plot(ax=ax)  # Берем срез данных

        st.pyplot(fig)
    else:
        st.error(f"Файлы не найдены в папке {DATA_DIR}. Положите туда реальный .nc или .ionex файл.")