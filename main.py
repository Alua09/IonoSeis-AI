import streamlit as st
import requests
import gzip
import shutil
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis AI: Конкурс")
st.title("🛰 IonoSeis AI: Аналитика ионосферы и сейсмики")


# --- ФУНКЦИИ ---
def get_kp_index():
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
        data = requests.get(url, timeout=5).json()
        return float(data[-1][1])
    except:
        return None


def parse_upc_ionex(file_path):
    with gzip.open(file_path, 'rb') as f_in:
        with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
    tec_values = []
    with open("data.ionex", 'r', errors='ignore') as f:
        in_block = False
        for line in f:
            if 'START OF TEC MAP' in line:
                in_block = True
            elif 'END OF TEC MAP' in line:
                in_block = False
            elif in_block and not any(x in line for x in ['LAT/LON1/LON2', 'EPOCH', 'START', 'END']):
                for p in line.split():
                    try:
                        val = float(p)
                        if val < 9000: tec_values.append(val)
                    except:
                        continue
    return np.array(tec_values[:5183]).reshape((71, 73))


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ОБНОВИТЬ ДАННЫЕ В МОМЕНТЕ"):
    with st.spinner("Загрузка данных..."):
        # 1. Kp-индекс
        kp = get_kp_index()
        st.metric("Kp-индекс (NOAA)", kp if kp else "Нет данных")

        # 2. Ионосфера (Динамический поиск файла)
        # Генерируем дату для URL NASA
        now = datetime.now()
        day_of_year = now.strftime("%j")
        year = now.strftime("%y")
        # Прямая ссылка на IONEX
        url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/{now.year}/{day_of_year}/coDG{day_of_year}0.{year}i.gz"

        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open("temp.gz", "wb") as f:
                    f.write(r.content)
                grid = parse_upc_ionex("temp.gz")
                val = grid[int((43.25 + 87.5) / 2.5), int((76.92 + 180) / 5.0)]
                st.metric("VTEC над Алматы", f"{val:.2f} TECU")
            else:
                st.warning("Данные ионосферы временно недоступны (сервер NASA).")
        except:
            st.error("Ошибка сети при обращении к NASA.")

        # 3. Сейсмика (USGS)
        st.subheader("📉 Сейсмика (Алматы 1000 км)")
        try:
            r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&limit=20&minmagnitude=2")
            df = pd.read_csv(io.StringIO(r.text))
            st.dataframe(df[['time', 'place', 'mag']])
        except:
            st.info("Сейсмически спокойно.")

# Обучающая информация для конкурса
st.markdown("---")
st.write("Механизм связи литосферы и ионосферы:")