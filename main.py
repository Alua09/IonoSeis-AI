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
    with st.spinner("Поиск актуальных данных в NASA..."):
        try:
            # 1. Поиск с ограничением по времени (чтобы не получать 404 ошибки)
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=('2026-05-01', '2026-05-30'),  # Можно задать конкретный месяц
                count=1
            )

            if not results:
                st.error("Данные за этот период не найдены.")
            else:
                files = earthaccess.download(results, "data")
                path = files[0]

                # Чтение файла
                ds = xr.open_dataset(path)
                fig, ax = plt.subplots()
                ds['TEC'].isel(time=0).plot(ax=ax)
                st.pyplot(fig)
                st.success("Данные успешно получены!")
        except Exception as e:
            st.error(f"Ошибка при скачивании: {e}")