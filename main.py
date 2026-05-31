import streamlit as st
import earthaccess
import os
import requests
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis AI: Мониторинг VTEC")


def setup_earthdata_auth():
    """Создает файл .netrc для автоматической авторизации"""
    netrc_content = (
        f"machine urs.earthdata.nasa.gov\n"
        f"login {st.secrets['EARTHDATA_USERNAME']}\n"
        f"password {st.secrets['EARTHDATA_PASSWORD']}"
    )
    # Записываем в домашнюю директорию
    netrc_path = os.path.expanduser("~/.netrc")
    with open(netrc_path, "w") as f:
        f.write(netrc_content)
    # Устанавливаем права доступа (важно для Linux/Cloud)
    os.chmod(netrc_path, 0o600)

    # Теперь логинимся без явной передачи аргументов
    return earthaccess.login(strategy="netrc")


if st.button("🚀 ЗАПУСК МОНИТОРИНГА"):
    try:
        with st.spinner("Авторизация и поиск данных..."):
            setup_earthdata_auth()

            # Поиск данных
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(datetime.now(), datetime.now()),
                count=1
            )

            if not results:
                st.error("Данные не найдены. Проверьте настройки коллекции.")
                st.stop()

            # Скачивание напрямую через библиотеку
            files = earthaccess.download(results, "./tmp")

            st.success(f"Файл скачан: {files[0]}")
            st.write("Теперь вы можете использовать парсер для обработки этого файла.")

    except Exception as e:
        st.error(f"Ошибка: {e}")