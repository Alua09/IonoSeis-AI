import streamlit as st
import requests
import gzip
import shutil
import numpy as np
import pandas as pd
import io
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Debug Mode")
st.title("🛰 IonoSeis AI: Отладка доступа к NASA")


# --- ФУНКЦИИ ---
def get_ionex_debug():
    # Пробуем вчерашний день, так как за сегодня файлов может не быть
    target_date = datetime.now() - timedelta(days=1)
    day = target_date.strftime("%j")
    year = target_date.strftime("%y")
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/{target_date.year}/{day}/coDG{day}0.{year}i.gz"

    # Пытаемся получить логин/пароль из секретов
    try:
        user = st.secrets["EARTHDATA_USERNAME"]
        pwd = st.secrets["EARTHDATA_PASSWORD"]
    except:
        return "Ошибка: Логин/Пароль не найдены в Secrets", None

    # Запрос
    response = requests.get(url, auth=(user, pwd), timeout=20)

    # Анализ ответа
    if response.status_code == 200:
        return "Успех (200)", response.content
    else:
        return f"Ошибка HTTP {response.status_code}", response.content[:500]  # Первые 500 байт


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ПРОВЕРИТЬ СОЕДИНЕНИЕ"):
    status, content = get_ionex_debug()
    st.write(f"### Статус: {status}")

    if isinstance(content, bytes):
        if content.startswith(b'\x1f\x8b'):
            st.success("Файл успешно получен (Gzip формат).")
        else:
            st.error("Получен НЕ архив. Возможно, это страница авторизации:")
            st.code(content.decode('utf-8', errors='ignore'))
    else:
        st.error(content)

st.info("""
**Что делать:**
Если вы увидите в поле `st.code` текст типа "Authentication Required" или "Earthdata Login", 
значит, ваш логин или пароль, хранящийся в Secrets, **не проходит** на сервере NASA.
Проверьте их в настройках Streamlit Cloud (Settings -> Secrets).
""")