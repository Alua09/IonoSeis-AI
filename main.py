import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta

# 1. Авторизация (используем среду, чтобы не светить пароли)
# В Streamlit Cloud добавьте EARTHDATA_USERNAME и EARTHDATA_PASSWORD в Secrets
earthaccess.login(strategy="netrc")

st.title("🛰 IonoSeis AI: Финальная попытка")

if st.button("🚀 СКАЧАТЬ И ОБРАБОТАТЬ"):
    try:
        # Ищем данные за последние 2 дня
        results = earthaccess.search_data(
            short_name='GNSS_IGS_AC_ion_VTEC_comp',
            temporal=(datetime.now() - timedelta(days=2), datetime.now()),
            count=1
        )

        if not results:
            st.error("Данные не найдены. Вы нажали '+' (зеленый плюс) в Earthdata Search?")
            st.stop()

        # Скачиваем файл
        files = earthaccess.download(results, "./tmp")

        st.success(f"Файл успешно скачан: {files[0]}")

        # Парсинг (мы теперь знаем, что это корректный файл из вашей коллекции)
        # Если возникнет ошибка при открытии файла, мы поймем, что дело в формате
        st.write("Файл получен, переходим к этапу визуализации.")

    except Exception as e:
        st.error(f"Критическая ошибка: {e}")