import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide", page_title="IonoSeis Pro: Стабильный")
st.title("🛰 IonoSeis Pro: Мониторинг")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92


# --- ФУНКЦИИ ---
def get_kp_robust():
    # Используем альтернативный API для Kp-индекса
    try:
        url = "https://kp.gfz-potsdam.de/app/files/Kp_ap_Ap_SN_F10.7_nowcast.json"
        data = requests.get(url, timeout=10).json()
        return float(data[-1][1])
    except:
        return None


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ОБНОВИТЬ СИСТЕМУ"):
    col1, col2 = st.columns(2)

    with col1:
        # 1. Kp-Индекс
        kp = get_kp_robust()
        st.metric("Глобальный Kp-индекс", kp if kp else "Данные недоступны")

        # 2. Ионосфера (NASA GIBS - карта)
        st.subheader("Глобальная карта ионосферы (NASA)")
        st.image(
            "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYER=GPM_3IMERGHH_Tb_Calibration&BBOX=-90,-180,90,180&WIDTH=800&HEIGHT=400&FORMAT=image/png")

    with col2:
        # 3. Сейсмика
        st.subheader("Сейсмика Алматы (1000 км)")
        quakes = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=100").json()

        for f in quakes['features']:
            lon, lat = f['geometry']['coordinates'][:2]
            dist = ((lat - ALMATY_LAT) ** 2 + (lon - ALMATY_LON) ** 2) ** 0.5 * 111
            if dist < 1000 and f['properties']['mag'] > 2.0:
                # Цветовая индикация по магнитуде
                mag = f['properties']['mag']
                text = f"🔹 {f['properties']['place']} | M: {mag} | {round(dist)} км"
                if mag >= 4.0:
                    st.error(f"⚠️ {text}")
                else:
                    st.write(text)

st.sidebar.info("Система работает в режиме прямого подключения к научным архивам.")