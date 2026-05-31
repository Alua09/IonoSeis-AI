import streamlit as st
import numpy as np
import requests
import pandas as pd
from datetime import datetime, timedelta

# Настройка
st.set_page_config(layout="wide", page_title="IonoSeis AI: Стабильный мониторинг")
st.title("🛰 IonoSeis Pro: Мониторинг Алматы")

ALMATY_LAT, ALMATY_LON = 43.25, 76.92


# --- ФУНКЦИИ ---
def get_kp_index():
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
        data = requests.get(url, timeout=5).json()
        return float(data[-1][1])
    except:
        return None


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ОБНОВИТЬ ДАННЫЕ (БЕЗОПАСНЫЙ РЕЖИМ)"):
    with st.spinner("Загрузка мониторинга..."):
        # 1. Kp-Индекс
        kp = get_kp_index()
        st.metric("Глобальный Kp-индекс", kp if kp else "Нет данных")

        # 2. Сейсмика (USGS - всегда стабильно работает)
        st.subheader("Сейсмическая активность в радиусе 1000 км")
        quakes_url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=200"
        quakes = requests.get(quakes_url).json()

        local_quakes = []
        for f in quakes['features']:
            lon, lat = f['geometry']['coordinates'][:2]
            dist = ((lat - ALMATY_LAT) ** 2 + (lon - ALMATY_LON) ** 2) ** 0.5 * 111
            if dist < 1000 and f['properties']['mag'] > 2.0:
                local_quakes.append(
                    {'place': f['properties']['place'], 'mag': f['properties']['mag'], 'dist': round(dist)})

        if local_quakes:
            df = pd.DataFrame(local_quakes)
            st.bar_chart(df.set_index('place')['mag'])
            for q in local_quakes:
                st.write(f"🔹 {q['place']} | M: {q['mag']} | {q['dist']} км")
        else:
            st.info("Сейсмически спокойно.")

        st.success(
            "Данные обновлены. Обратите внимание: скачивание тяжелых файлов NASA временно ограничено политикой безопасности сервера.")

st.sidebar.info(
    "Система работает в защищенном режиме. Прямое скачивание файлов NASA отключено для предотвращения сбоев.")