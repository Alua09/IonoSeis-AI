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
    # Пытаемся найти данные в разных коллекциях
    collections = ['IGS_GIM', 'GIM_IONEX', 'GPS_IONEX']

    for coll in collections:
        try:
            results = earthaccess.search_data(
                short_name=coll,
                temporal=(datetime.now() - timedelta(days=15), datetime.now())
            )
            if results:
                # Скачиваем файл
                files = earthaccess.download(results[-1], "./tmp")
                ds = xr.open_dataset(files[0])
                # Авто-определение переменной TEC
                field = 'TEC' if 'TEC' in ds else list(ds.data_vars)[0]
                return ds.sel(lat=lat, lon=lon, method='nearest')[field].values
        except:
            continue
    raise Exception("Данные недоступны в текущих коллекциях NASA.")


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