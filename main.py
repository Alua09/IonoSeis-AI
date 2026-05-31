import streamlit as st
import requests


def fetch_ionex_data():
    day = "151"  # Например, 151
    year = "26"
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/2026/{day}/igsg{day}0.{year}i.Z"

    # Ключевой момент: используем Session для сохранения куки авторизации
    session = requests.Session()
    session.auth = (st.secrets["EARTHDATA_USERNAME"], st.secrets["EARTHDATA_PASSWORD"])

    # Сначала заходим на сервер авторизации, а потом скачиваем файл
    response = session.get(url, stream=True)

    # Проверка, не попали ли мы снова на страницу логина
    if "Earthdata Login" in response.text[:500]:
        return None, "Ошибка: Авторизация не прошла, сервер вернул страницу логина."

    return response.content, "Успех!"

# Используйте этот код в своей кнопке