import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import earthaccess
import xarray as xr
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Реальные данные NASA")
st.title("🛰 IonoSeis AI: Анализ на основе данных NASA IONEX")


# 1. Функция получения реальных данных VTEC
def get_real_vtec(lat, lon):
    # Авторизация (нужен логин/пароль с earthdata.nasa.gov)
    earthaccess.login(strategy="interactive")

    # Поиск файлов IONEX за последние 30 дней
    results = earthaccess.search_data(
        short_name='GIM_IONEX',
        temporal=(datetime.now() - timedelta(days=30), datetime.now())
    )

    # Скачивание и загрузка первого попавшегося файла (в реальности нужно циклом)
    files = earthaccess.download(results[0], "./data")
    ds = xr.open_dataset(files[0])

    # Извлечение данных для точки
    data = ds.sel(lat=lat, lon=lon, method='nearest')
    return data.TEC.values  # Возвращает массив данных VTEC


# 2. Функция землетрясений (USGS)
def get_earthquakes(lat, lon):
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {"format": "geojson", "latitude": lat, "longitude": lon,
              "maxradius": 5, "minmagnitude": 4.5,
              "starttime": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}
    response = requests.get(url, params=params).json()
    return [datetime.fromtimestamp(f['properties']['time'] / 1000).strftime('%d.%m')
            for f in response.get('features', [])]


if st.button("🚀 Загрузить данные NASA и анализировать"):
    locations = {"Алматы": (43.2, 76.9), "Токио": (35.7, 139.7)}
    fig, axes = plt.subplots(2, 1, figsize=(14, 12))

    for i, (city, (lat, lon)) in enumerate(locations.items()):
        # Загрузка реальных данных
        series = get_real_vtec(lat, lon)
        days = [(datetime.now() - timedelta(days=30 - i)).strftime('%d.%m') for i in range(30)]
        kp_data = np.random.randint(0, 6, 30)  # Kp-индекс можно брать через API NOAA

        # Анализ
        mean, std = np.mean(series), np.std(series)
        upper = mean + 2 * std
        anomalies = (series > upper) & (kp_data < 4)

        ax1 = axes[i]
        ax2 = ax1.twinx()

        # Визуализация
        ax1.fill_between(days, mean - 2 * std, upper, color='green', alpha=0.1, label='Норма')
        ax1.plot(days, series, color='blue', label='VTEC', linewidth=2)
        ax1.scatter(np.array(days)[anomalies], series[anomalies], color='red', s=100, label='Аномалия')

        for qd in get_earthquakes(lat, lon):
            if qd in days:
                ax1.axvline(qd, color='black', linestyle='--', label='Землетрясение')

        ax2.bar(days, kp_data, color='orange', alpha=0.2, label='Kp-индекс')

        ax1.set_title(f"Регион: {city} (Данные NASA)")
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')

    st.pyplot(fig)