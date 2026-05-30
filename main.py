import streamlit as st
import earthaccess
import os
import gzip
import shutil
import matplotlib.pyplot as plt
import xarray as xr
import random

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ данных из космоса")

DATA_DIR = os.path.join(os.getcwd(), "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def download_and_process():
    # 1. Поиск данных
    results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', count=1)
    if not results: return None

    # 2. Скачивание
    files = earthaccess.download(results, DATA_DIR)
    file_path = files[0]

    # 3. Распаковка (более надежный метод)
    unpacked_path = file_path[:-3] if file_path.endswith('.gz') else file_path

    with gzip.open(file_path, 'rb') as f_in:
        with open(unpacked_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    return unpacked_path


if st.button("🚀 Скачать и проанализировать данные"):
    with st.spinner("Связь со спутниками..."):
        try:
            file_path = download_and_process()
            # Читаем файл через xarray
            ds = xr.open_dataset(file_path)

            # Визуализация
            fig, ax = plt.subplots(figsize=(10, 5))
            # Берем данные по TEC (Total Electron Content)
            var = list(ds.data_vars)[0]
            ds[var].isel(time=0).plot(ax=ax)

            st.pyplot(fig)
            st.success("Данные успешно получены!")
        except Exception as e:
            st.error(f"Ошибка обработки: {e}")