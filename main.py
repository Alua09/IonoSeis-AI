import streamlit as st
import earthaccess
import os
import gzip
import shutil
import matplotlib.pyplot as plt
import xarray as xr

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ данных из космоса")

DATA_DIR = os.path.join(os.getcwd(), "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def download_and_process():
    # Ищем данные
    results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', count=1)
    if not results:
        return None, "Данные не найдены"

    # Скачиваем
    files = earthaccess.download(results, DATA_DIR)
    if not files:
        return None, "Ошибка скачивания"

    file_path = files[0]
    unpacked_path = file_path[:-3] if file_path.endswith('.gz') else file_path

    # Распаковка
    with gzip.open(file_path, 'rb') as f_in:
        with open(unpacked_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    return unpacked_path, None


if st.button("🚀 Скачать и проанализировать данные"):
    with st.spinner("Связь со спутниками..."):
        path, error = download_and_process()
        if error:
            st.error(error)
        else:
            try:
                ds = xr.open_dataset(path)
                fig, ax = plt.subplots(figsize=(10, 5))
                var = list(ds.data_vars)[0]
                ds[var].isel(time=0).plot(ax=ax)
                st.pyplot(fig)
                st.success("Анализ выполнен!")
            except Exception as e:
                st.error(f"Ошибка чтения файла: {e}")