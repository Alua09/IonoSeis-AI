import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

# --- ВАШ РАБОЧИЙ КОД ---
st.set_page_config(layout="wide")
st.title("🛰 IonoSeis AI: Анализ VTEC и Сейсмо-событий")

locations = {"Алматы": (43.2, 76.9), "Токио": (35.7, 139.7)}


# Функция получения землетрясений
def get_earthquakes(lat, lon):
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "latitude": lat,
        "longitude": lon,
        "maxradius": 5,  # Радиус поиска в градусах
        "minmagnitude": 4.5,
        "starttime": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    }
    try:
        data = requests.get(url, params=params).json()
        return [datetime.fromtimestamp(f['properties']['time'] / 1000).strftime('%d.%m')
                for f in data.get('features', [])]
    except:
        return []


if st.button("🚀 Построить графики с учетом землетрясений"):
    fig, axes = plt.subplots(2, 1, figsize=(14, 12))
    dates = [(datetime.now() - timedelta(days=30 - i)).strftime('%d.%m') for i in range(30)]

    for i, (city, (lat, lon)) in enumerate(locations.items()):
        # ВАШИ ДАННЫЕ (здесь останется интеграция с IONEX)
        series = 15 + 5 * np.sin(np.linspace(0, 5, 30)) + np.random.normal(0, 0.5, 30)
        kp_data = np.random.randint(0, 6, 30)

        quake_dates = get_earthquakes(lat, lon)  # Получаем реальные события

        ax1 = axes[i]
        ax2 = ax1.twinx()

        # Основной график
        ax1.plot(dates, series, color='blue', label='VTEC')
        ax2.bar(dates, kp_data, color='orange', alpha=0.3, label='Kp-индекс')

        # Накладываем вертикальные линии землетрясений
        for qd in quake_dates:
            if qd in dates:
                ax1.axvline(qd, color='black', linestyle='--', linewidth=2, label='Землетрясение')

        ax1.set_title(f"Мониторинг: {city}")
        ax1.legend(loc='upper left')

    st.pyplot(fig)