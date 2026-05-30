import streamlit as st
import earthaccess
import os
import gzip
import shutil
import matplotlib.pyplot as plt
import xarray as xr

# Используем секреты из Streamlit
username = st.secrets["EARTHDATA_USERNAME"]
password = st.secrets["EARTHDATA_PASSWORD"]

# Авторизация
auth = earthaccess.login(strategy="password", username=username, password=password)

st.title("🛰 IonoSeis AI: Анализ")

if st.button("🚀 Анализировать данные IGS"):
    with st.spinner("Скачивание из NASA..."):
        try:
            # Поиск и скачивание
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', count=1)
            files = earthaccess.download(results, "data")

            # Распаковка и чтение (как раньше)
            path = files[0]
            unpacked = path.replace('.gz', '')
            # ... остальная логика визуализации ...
            st.success("Данные загружены!")
        except Exception as e:
            st.error(f"Ошибка: {e}")