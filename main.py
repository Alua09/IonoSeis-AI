import streamlit as st
import earthaccess
import os
import matplotlib.pyplot as plt
import xarray as xr

st.title("🛰 IonoSeis AI: Тест связи")

# Проверка секретов
try:
    user = st.secrets["EARTHDATA_USERNAME"]
    st.write("Секреты успешно загружены!")
except Exception as e:
    st.error("Секреты НЕ найдены! Зайдите в Settings -> Secrets на сайте.")

if st.button("🚀 Тест связи с NASA"):
    with st.spinner("Авторизация..."):
        try:
            earthaccess.login(strategy="password",
                              username=st.secrets["EARTHDATA_USERNAME"],
                              password=st.secrets["EARTHDATA_PASSWORD"])
            st.success("Авторизация прошла успешно!")

            # Поиск
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', count=1)
            st.write(f"Найдено файлов: {len(results)}")
        except Exception as e:
            st.error(f"Ошибка: {e}")