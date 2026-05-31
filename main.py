import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

st.set_page_config(layout="wide", page_title="IonoSeis Pro")
st.title("🛰 IonoSeis Pro: Мониторинг")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92


def get_kp_scraped():
    # Парсинг страницы SWPC NOAA напрямую
    try:
        url = "https://www.swpc.noaa.gov/products/planetary-k-index"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Ищем блок с последним значением Kp
        value = soup.find('div', class_='current-k-index')
        return value.text.strip() if value else "Обновление..."
    except:
        return "Ошибка сети"


if st.button("🚀 ЗАПУСТИТЬ СКАНИРОВАНИЕ"):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Геомагнитный фон")
        st.metric("Kp-индекс (текущий)", get_kp_scraped())
        st.subheader("Карта ионосферы")
        st.image("https://services.swpc.noaa.gov/images/animations/geospace/geospace_kp.gif")

    with col2:
        st.subheader("Сейсмика (Алматы 1000 км)")
        # USGS GeoJSON работает стабильно
        quakes = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100").json()
        for f in quakes['features']:
            lon, lat = f['geometry']['coordinates'][:2]
            dist = ((lat - ALMATY_LAT) ** 2 + (lon - ALMATY_LON) ** 2) ** 0.5 * 111
            if dist < 1000 and f['properties']['mag'] > 2.0:
                text = f"🔹 {f['properties']['place']} | M: {f['properties']['mag']} | {round(dist)} км"
                st.write(text)

st.sidebar.info("Система переключена на прямой парсинг источников.")