import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import earthaccess
import gzip
import shutil
import os
import requests
import io
import pandas as pd

st.set_page_config(layout="wide", page_title="IonoSeis AI: Final")
st.title("🛰 IonoSeis AI: Мониторинг литосферно-ионосферной связи")


# --- ФУНКЦИИ ---
def get_ionex_data():
    """Скачивание с NASA или возврат кэша из проекта"""
    try:
        # Пытаемся получить данные через earthaccess
        results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', count=1)
        session = earthaccess.login(persist=True).get_session()
        response = session.get(results[0].data_links()[0], stream=True)
        with open("data.ionex.gz", 'wb') as f:
            f.write(response.content)
        return "data.ionex.gz"
    except:
        return "backup_ionex.gz" if os.path.exists("backup_ionex.gz") else None


def parse_and_clean(file_path):
    """Парсинг с фильтрацией мусора и заполнением пустот"""
    with gzip.open(file_path, 'rb') as f_in:
        with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)

    tec = []
    with open("data.ionex", 'r', errors='ignore') as f:
        in_block = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_block = True
            elif 'END OF TEC MAP' in line:
                in_block = False
            elif in_block and not any(x in line for x in ['LAT/LON', 'EPOCH']):
                for p in line.split():
                    try:
                        val = float(p)
                        # Фильтруем физически невозможные значения
                        tec.append(val if 0 < val < 200 else np.nan)
                    except:
                        continue

    data = np.array(tec, dtype=float)
    # Заполняем пропуски средним значением для чистоты карты
    data[np.isnan(data)] = np.nanmean(data)
    return data[:5183].reshape((71, 73))


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ЗАПУСТИТЬ АНАЛИЗ"):
    with st.spinner("Синхронизация с NASA и USGS..."):
        file_path = get_ionex_data()
        if file_path:
            grid = parse_and_clean(file_path)
            final_grid = np.flipud(grid.T)

            # Визуализация
            fig, ax = plt.subplots(figsize=(10, 4))
            im = ax.imshow(final_grid, cmap='inferno', origin='lower', aspect='auto', extent=[-180, 180, -87.5, 87.5])
            plt.colorbar(im, label='VTEC (TECU)')
            st.pyplot(fig)

            # Сейсмика
            st.subheader("Сейсмическая активность")
            r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&limit=5&minmagnitude=2")
            df = pd.read_csv(io.StringIO(r.text))
            st.dataframe(df[['place', 'mag', 'time']])
        else:
            st.error("Данные недоступны.")

st.markdown("---")
st.write(
    "Механизм мониторинга: анализ возмущений полного электронного содержания (VTEC) перед сейсмическими событиями.")