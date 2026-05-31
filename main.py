import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime

st.set_page_config(layout="wide")
st.title("🛰 IonoSeis AI: Отладчик соединений NASA")

# Данные для входа
USER = st.secrets.get("EARTHDATA_USERNAME", "")
PASSWORD = st.secrets.get("EARTHDATA_PASSWORD", "")


def check_and_fetch():
    # На 31 мая 2026 года (сегодня) год 2026, день 151
    day_of_year = datetime.now().strftime("%j")
    year = datetime.now().strftime("%y")

    # Пытаемся сформировать правильный URL
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/2026/{day_of_year}/igsg{day_of_year}0.{year}i.Z"

    st.write(f"Пробую скачать по адресу: {url}")

    session = requests.Session()
    session.auth = (USER, PASSWORD)

    response = session.get(url, stream=True)

    if response.status_code == 200:
        with open("data.ionex", 'wb') as f:
            f.write(response.content)
        return True, "Файл успешно скачан!"
    else:
        return False, f"Ошибка {response.status_code}. Возможно, файл еще не появился в архиве."


if st.button("🚀 ПРОВЕРИТЬ СОЕДИНЕНИЕ"):
    success, message = check_and_fetch()
    if success:
        st.success(message)
    else:
        st.error(message)
        st.info(
            "💡 Совет: Скопируйте ссылку выше и откройте её в браузере вручную. Если браузер тоже выдаст ошибку, значит, проблема в ссылке.")