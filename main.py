import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import earthaccess
import os
import xarray as xr
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Анализ")


# --- «ХИТРАЯ» ФУНКЦИЯ АВТОРИЗАЦИИ ---
def authenticate():
    user = st.secrets.get("EARTHDATA_USERNAME") or os.getenv('EARTHDATA_USERNAME')
    pwd = st.secrets.get("EARTHDATA_PASSWORD") or os.getenv('EARTHDATA_PASSWORD')

    # Создаем файл .netrc в домашней директории программы
    netrc_path = os.path.expanduser("~/.netrc")
    with open(netrc_path, "w") as f:
        f.write(f"machine urs.earthdata.nasa.gov login {user} password {pwd}")

    # Теперь earthaccess найдет файл, который мы только что создали
    earthaccess.login(strategy="netrc")


# --- ОСТАЛЬНОЙ КОД ---
def get_latest_data(lat, lon):
    results = earthaccess.search_data(
        short_name='GIM_IONEX',
        temporal=(datetime.now() - timedelta(days=2), datetime.now())
    )
    files = earthaccess.download(results[0], "./tmp")
    ds = xr.open_dataset(files[0])
    return ds.sel(lat=lat, lon=lon, method='nearest').TEC.values


if st.button("🚀 ЗАГРУЗИТЬ И АНАЛИЗИРОВАТЬ"):
    try:
        with st.spinner("Авторизация..."):
            authenticate()
            st.write("✅ Авторизация успешна. Скачивание данных...")

            locations = {"Алматы": (43.2, 76.9), "Токио": (35.7, 139.7)}
            fig, axes = plt.subplots(2, 1, figsize=(14, 12))
            dates = [(datetime.now() - timedelta(days=30 - i)).strftime('%d.%m') for i in range(30)]

            for i, (city, (lat, lon)) in enumerate(locations.items()):
                series = get_latest_data(lat, lon)[:30]
                kp_data = np.random.randint(0, 6, 30)

                mean, std = np.mean(series), np.std(series)
                upper = mean + 2 * std
                anomalies = (series > upper) & (kp_data < 4)

                ax1 = axes[i]
                ax2 = ax1.twinx()
                ax1.plot(dates, series, label='VTEC', color='blue')
                ax1.scatter(np.array(dates)[anomalies], series[anomalies], color='red', s=100, label='Аномалия')
                ax2.bar(dates, kp_data, color='orange', alpha=0.2, label='Kp-индекс')

                ax1.set_title(f"Регион: {city}")
                ax1.legend();
                ax2.legend()

            st.pyplot(fig)
    except Exception as e:
        st.error(f"Произошла ошибка: {e}")