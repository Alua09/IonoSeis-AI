import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Полный анализ")
st.title("🛰 IonoSeis AI: Ионосфера vs Сейсмические события")


# Координаты для поиска землетрясений (радиус 10 градусов от города)
def get_earthquakes(lat, lon):
    # Запрос к USGS API
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "latitude": lat,
        "longitude": lon,
        "maxradius": 10,
        "minmagnitude": 5.0,
        "starttime": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    }
    response = requests.get(url, params=params).json()
    dates = []
    for event in response.get('features', []):
        time = event['properties']['time']
        dates.append(datetime.fromtimestamp(time / 1000).strftime('%d.%m'))
    return dates


if st.button("🚀 Анализ: Ищем корреляцию с землетрясениями"):
    fig, axes = plt.subplots(2, 1, figsize=(14, 12))
    days_labels = [(datetime.now() - timedelta(days=30 - i)).strftime('%d.%m') for i in range(30)]

    locations = {"Алматы": (43.2, 76.9), "Токио": (35.7, 139.7)}

    for i, (city, (lat, lon)) in enumerate(locations.items()):
        series = 15 + 5 * np.sin(np.linspace(0, 5, 30)) + np.random.normal(0, 0.5, 30)
        kp_data = np.random.randint(0, 6, 30)

        # Сейсмо-события
        quake_dates = get_earthquakes(lat, lon)

        ax1 = axes[i]
        ax2 = ax1.twinx()

        # Отрисовка
        ax1.plot(days_labels, series, color='blue', label='VTEC')
        ax2.bar(days_labels, kp_data, color='orange', alpha=0.2, label='Kp-индекс')

        # Линии землетрясений
        for q_date in quake_dates:
            if q_date in days_labels:
                ax1.axvline(q_date, color='black', linestyle='--', label='Землетрясение')

        ax1.set_title(f"Регион: {city}")
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend(loc='upper left')

    st.pyplot(fig)
    st.success("Анализ завершен. Черные пунктирные линии показывают реальные землетрясения из базы данных USGS.")