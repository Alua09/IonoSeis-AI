import streamlit as st
import earthaccess
import os
import matplotlib.pyplot as plt
import xarray as xr

st.title("🛰 IonoSeis AI: Анализ")

# Просто вызываем login() без аргументов.
# Библиотека сама найдет переменные EARTHDATA_USERNAME и EARTHDATA_PASSWORD в окружении.
try:
    earthaccess.login()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}")

if st.button("🚀 Анализировать данные IGS"):
    with st.spinner("Скачивание из NASA..."):
        try:
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', count=1)
            if not results:
                st.error("Данные не найдены")
            else:
                files = earthaccess.download(results, "data")
                path = files[0]

                # Работа с файлом
                ds = xr.open_dataset(path)
                fig, ax = plt.subplots()
                ds['TEC'].isel(time=0).plot(ax=ax)
                st.pyplot(fig)
                st.success("Данные успешно загружены!")
        except Exception as e:
            st.error(f"Ошибка при скачивании или чтении: {e}")