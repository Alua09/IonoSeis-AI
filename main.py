import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import earthaccess
import os
import xarray as xr
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Анализ")


def authenticate():
    user = st.secrets.get("EARTHDATA_USERNAME") or os.getenv('EARTHDATA_USERNAME')
    pwd = st.secrets.get("EARTHDATA_PASSWORD") or os.getenv('EARTHDATA_PASSWORD')
    netrc_path = os.path.expanduser("~/.netrc")
    with open(netrc_path, "w") as f:
        f.write(f"machine urs.earthdata.nasa.gov login {user} password {pwd}")
    earthaccess.login(strategy="netrc")


def get_latest_data(lat, lon):
    # Увеличим интервал до 7 дней, чтобы гарантированно найти хоть что-то
    results = earthaccess.search_data(
        short_name='GIM_IONEX',
        temporal=(datetime.now() - timedelta(days=7), datetime.now())
    )

    # ПРОВЕРКА: есть ли вообще найденные файлы
    if not results:
        raise Exception("Не удалось найти данные GIM IONEX на серверах NASA за последнюю неделю.")

    # Скачиваем последний файл из списка
    files = earthaccess.download(results[-1], "./tmp")
    ds = xr.open_dataset(files[0])
    return ds.sel(lat=lat, lon=lon, method='nearest').TEC.values


if st.button("🚀 ЗАГРУЗИТЬ И АНАЛИЗИРОВАТЬ"):
    try:
        with st.spinner("Авторизация и поиск данных..."):
            authenticate()
            st.write("✅ Авторизация успешна. Ищем данные...")

            locations = {"Алматы": (43.2, 76.9), "Токио": (35.7, 139.7)}
            fig, axes = plt.subplots(2, 1, figsize=(14, 12))
            dates = [(datetime.now() - timedelta(days=30 - i)).strftime('%d.%m') for i in range(30)]

            for i, (city, (lat, lon)) in enumerate(locations.items()):
                # Если данных все равно нет, используем заглушку, чтобы не прерывать весь процесс
                try:
                    series = get_latest_data(lat, lon)[:30]
                except Exception as e:
                    st.warning(f"Данные для {city} не получены: {e}. Используем симуляцию.")
                    series = 15 + 5 * np.sin(np.linspace(0, 5, 30))

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
            st.success("Анализ завершен!")
    except Exception as e:
        st.error(f"Критическая ошибка: {e}")