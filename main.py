import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime

st.set_page_config(layout="wide")
st.title("🛰 IonoSeis AI: Детектор структуры файлов")

USER = st.secrets.get("EARTHDATA_USERNAME", "")
PASSWORD = st.secrets.get("EARTHDATA_PASSWORD", "")


def debug_fetch():
    day = datetime.now().strftime("%j")
    year = datetime.now().strftime("%y")
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/2026/{day}/igsg{day}0.{year}i.Z"

    response = requests.get(url, auth=(USER, PASSWORD))
    if response.status_code != 200:
        return f"Ошибка HTTP {response.status_code}"

    content = response.content.decode('latin-1', errors='ignore')

    # ВОТ ОНИ - ПЕРВЫЕ 500 СИМВОЛОВ ФАЙЛА
    return content[:500]


if st.button("🚀 ПОКАЗАТЬ, ЧТО ВНУТРИ"):
    st.text(debug_fetch())