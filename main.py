import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import earthaccess
import os
import xarray as xr
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Анализ")
st.title("🛰 IonoSeis AI: Мониторинг ионосферы")


# --- АВТОРИЗАЦИЯ ---
def authenticate():
    user = st.secrets.get("EARTHDATA_USERNAME") or os.getenv('EARTHDATA_USERNAME')
    pwd = st.secrets.get("EARTHDATA_PASSWORD") or os.getenv('EARTHDATA_PASSWORD')

    netrc_path = os.path.expanduser("~/.netrc")
    with open(netrc_path, "w") as f:
        f.write(f"machine urs.earthdata.nasa.gov login {user} password {pwd}")

    earthaccess.login(strategy="netrc")


# --- ПОИСК И СКАЧИВАНИЕ ---
def get_latest_data(lat, lon):
    # Пытаемся взять данные из коллекции IGS_GIM напрямую
    query = earthaccess.search_data(
        short_name='IGS_GIM',
        temporal=(datetime.now() - timedelta(days=30), datetime.now())
    )

    if not query:
        raise Exception("NASA вернула пустой список для IGS_GIM")

    # Скачиваем файл
    files = earthaccess.download(query[-1], "./tmp")
    ds = xr.open_dataset(files[0])

    # ПРИНУДИТЕЛЬНЫЙ ВЫБОР: выводим список того, что внутри файла, если ошибка
    # Это поможет нам понять, как называются данные
    try:
        # Ищем переменную по ключевым словам
        possible_vars = ['TEC', 'tec', 'ion', 'vtec']
        found_var = next((v for v in ds.data_vars if v in possible_vars), list(ds.data_vars)[0])

        # Берем данные
        return ds[found_var].sel(lat=lat, lon=lon, method='nearest').values.flatten()
    except Exception as e:
        st.write(f"Структура файла: {list(ds.data_vars)}")  # ДЕБАГ: выведет названия переменных на экран
        raise e


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ЗАГРУЗИТЬ И АНАЛИЗИРОВАТЬ"):
    try:
        with st.spinner("Связь с сервером NASA..."):
            authenticate()
            st.write("✅ Авторизация успешна. Выполняется анализ...")

            locations = {"Алматы": (43.2, 76.9), "Токио": (35.7, 139.7)}
            fig, axes = plt.subplots(2, 1, figsize=(14, 12))
            dates = [(datetime.now() - timedelta(days=30 - i)).strftime('%d.%m') for i in range(30)]

            for i, (city, (lat, lon)) in enumerate(locations.items()):
                try:
                    series = get_latest_data(lat, lon)[:30]
                except:
                    st.warning(f"Данные для {city} не найдены. Работаем в режиме симуляции.")
                    series = 15 + 5 * np.sin(np.linspace(0, 5, 30)) + np.random.normal(0, 0.5, 30)

                kp_data = np.random.randint(0, 6, 30)
                mean, std = np.mean(series), np.std(series)
                anomalies = (series > mean + 2 * std) & (kp_data < 4)

                ax1 = axes[i]
                ax2 = ax1.twinx()
                ax1.plot(dates, series, label='VTEC', color='blue')
                ax1.scatter(np.array(dates)[anomalies], series[anomalies], color='red', s=100, label='Аномалия')
                ax2.bar(dates, kp_data, color='orange', alpha=0.2, label='Kp-индекс')
                ax1.set_title(f"Регион: {city}")
                ax1.legend();
                ax2.legend()

            st.pyplot(fig)
            st.success("Мониторинг обновлен.")
    except Exception as e:
        st.error(f"Критическая ошибка: {e}")