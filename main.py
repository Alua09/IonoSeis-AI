import streamlit as st
import requests
import pandas as pd

st.set_page_config(layout="wide", page_title="IonoSeis Pro")
st.title("🛰 IonoSeis Pro: Мониторинг")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92


# Прямое получение данных через надежный JSON API
def get_data():
    try:
        # Kp-индекс
        kp_url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
        kp_data = requests.get(kp_url, timeout=5).json()
        kp = kp_data[-1][1]

        # Сейсмика
        quake_url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100"
        quakes = requests.get(quake_url, timeout=5).json()

        return kp, quakes
    except:
        return None, None


if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    kp, quakes = get_data()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Геомагнитный фон")
        st.metric("Kp-индекс (текущий)", kp if kp else "Ошибка")

        st.subheader("Карта ионосферы")
        # Прямая ссылка на всегда доступный файл изображения NOAA
        st.image("https://services.swpc.noaa.gov/images/animations/geospace/geospace_kp.gif")

    with col2:
        st.subheader("Сейсмика (Алматы 1000 км)")
        if quakes:
            found = False
            for f in quakes['features']:
                lon, lat = f['geometry']['coordinates'][:2]
                dist = ((lat - ALMATY_LAT) ** 2 + (lon - ALMATY_LON) ** 2) ** 0.5 * 111
                if dist < 1000 and f['properties']['mag'] > 2.0:
                    st.write(f"🔹 {f['properties']['place']} | M: {f['properties']['mag']} | {round(dist)} км")
                    found = True
            if not found: st.info("В радиусе 1000 км событий нет.")
        else:
            st.error("Не удалось получить данные сейсмики.")