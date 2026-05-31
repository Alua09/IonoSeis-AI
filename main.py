import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import earthaccess
import os
from datetime import datetime

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis AI: Официальный мониторинг")
st.title("🛰 IonoSeis AI: Реальные данные NASA")


# --- ФУНКЦИЯ АВТОРИЗАЦИИ И СКАЧИВАНИЯ ---
def get_data_from_nasa():
    # 1. Авторизация через официальную библиотеку (самый надежный способ)
    auth = earthaccess.login(
        username=st.secrets["EARTHDATA_USERNAME"],
        password=st.secrets["EARTHDATA_PASSWORD"],
        strategy="interactive"  # или "netrc"
    )

    # 2. Поиск конкретного файла за сегодня
    day_of_year = datetime.now().strftime("%j")
    # Ищем коллекцию IGS IONEX
    results = earthaccess.search_data(
        short_name='GNSS_IGS_AC_ion_VTEC_comp',
        temporal=(datetime.now(), datetime.now()),
        count=1
    )

    if not results:
        return None

    # 3. Скачивание
    files = earthaccess.download(results, "./tmp")
    return files[0]


# --- ИНТЕРФЕЙС ---
# Кнопка будет активной по умолчанию
if st.button("🚀 ЗАПУСК МОНИТОРИНГА"):
    try:
        with st.spinner("Связь с сервером NASA..."):
            file_path = get_data_from_nasa()

            if file_path:
                st.success("Данные успешно получены!")
                # Чтение и визуализация (парсинг)
                # ... тут код парсинга, который мы отладили ранее ...
                st.write(f"Файл готов к обработке: {file_path}")
            else:
                st.error("Данные за сегодня еще не опубликованы в архиве NASA.")
    except Exception as e:
        st.error(f"Ошибка системы: {e}")