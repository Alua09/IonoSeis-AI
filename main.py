import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import requests
import gzip
import shutil
import os
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Final Monitor")
st.title("🛰 IonoSeis AI: Анализ ионосферы и сейсмоактивности")


# --- ФУНКЦИИ ---
def setup_auth():
    """Настройка авторизации через netrc"""
    netrc_path = os.path.expanduser("~/.netrc")
    with open(netrc_path, "w") as f:
        f.write(
            f"machine urs.earthdata.nasa.gov\nlogin {st.secrets['EARTHDATA_USERNAME']}\npassword {st.secrets['EARTHDATA_PASSWORD']}")
    os.chmod(netrc_path, 0o600)
    earthaccess.login(strategy="netrc")


def parse_and_clean(file_path):
    """Парсинг IONEX с очисткой данных"""
    if not file_path or not os.path.exists(file_path):
        return np.zeros((71, 73))

    try:
        with gzip.open(file_path, 'rb') as f_in:
            with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
    except:
        return np.zeros((71, 73))

    tec = []
    with open("data.ionex", 'r', errors='ignore') as f:
        in_block = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_block = True
            elif 'END OF TEC MAP' in line:
                in_block = False
            elif in_block and not any(x in line for x in ['LAT/LON', 'EPOCH', 'START', 'END']):
                for p in line.split():
                    try:
                        val = float(p)
                        tec.append(val if 0 < val < 300 else np.nan)
                    except:
                        continue

    data = np.array(tec, dtype=float)
    data[np.isnan(data)] = np.nanmean(data)
    return data[:5183].reshape((71, 73))


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ЗАПУСТИТЬ АНАЛИЗ"):
    with st.spinner("Синхронизация..."):
        try:
            # 1. Поиск данных
            today = datetime.now()
            start_date = (today - timedelta(days=2)).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')

            setup_auth()
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(start_date, end_date), count=1)

            if results:
                files = earthaccess.download(results, "./tmp")
                file_path = files[0]
            else:
                file_path = "backup_ionex.gz"
                st.warning("Актуальные данные не найдены, используется архив.")

            # 2. Обработка
            grid = parse_and_clean(file_path)

            # 3. Визуализация
            fig, ax = plt.subplots(figsize=(10, 6))
            im = ax.imshow(np.flipud(grid.T), cmap='inferno', interpolation='bicubic',
                           extent=[-180, 180, -87.5, 87.5], aspect='auto', alpha=0.9)

            # Фокус на Казахстан
            ax.set_xlim(40, 95)
            ax.set_ylim(35, 60)

            # Сейсмика
            quakes = requests.get(
                "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=5&limit=10").json()
            for f in quakes['features']:
                lon, lat = f['geometry']['coordinates'][:2]
                ax.scatter(lon, lat, color='white', marker='*', s=120, edgecolors='black')

            plt.colorbar(im, label='VTEC (TECU)')
            ax.set_title("Мониторинг ионосферы над Казахстаном")
            st.pyplot(fig)

        except Exception as e:
            st.error(f"Ошибка: {e}")

st.markdown("---")
st.write("Метод мониторинга основан на выявлении косейсмических ионосферных возмущений (TIDs).")