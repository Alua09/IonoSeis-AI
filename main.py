import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import requests
import os
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
st.title("🛰 IonoSeis AI: Мониторинг ионосферы")


# Настройки доступа
def setup_auth():
    # Проверка наличия секретов
    if 'EARTHDATA_USERNAME' not in st.secrets:
        st.error("Ошибка: Настройте EARTHDATA_USERNAME и PASSWORD в Secrets!")
        return False
    os.environ['EARTHDATA_USERNAME'] = st.secrets['EARTHDATA_USERNAME']
    os.environ['EARTHDATA_PASSWORD'] = st.secrets['EARTHDATA_PASSWORD']
    return True


if st.button("🚀 ЗАПУСК"):
    try:
        if not setup_auth(): st.stop()

        with st.spinner("Поиск данных..."):
            auth = earthaccess.login(strategy="environment")
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now() - timedelta(days=5), datetime.now())
            )

            if not results:
                st.warning("Данные на сервере не найдены. Попробуйте позже.")
                st.stop()

            st.write(f"Найдено файлов: {len(results)}")
            # Скачиваем без сложной распаковки для теста
            files = earthaccess.download(results[0:1], "./tmp")
            st.write(f"Файл загружен: {files[0]}")

            # Если файл не пустой
            if os.path.exists(files[0]):
                st.success("Данные успешно получены!")
                # Выводим первые 10 строк файла как текст
                with open(files[0], 'r', errors='ignore') as f:
                    content = f.readlines()[:10]
                    st.code("".join(content))

    except Exception as e:
        st.exception(e)  # Это покажет ошибку на экране, а не пустой экран