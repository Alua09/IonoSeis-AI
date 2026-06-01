import streamlit as st
import requests
import gzip
import shutil
import numpy as np
import pandas as pd
import io
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Monitor")
st.title("🛰 IonoSeis AI: Аналитика ионосферы и сейсмики")

# --- КОНФИГУРАЦИЯ ---
HEADERS = {'User-Agent': 'Mozilla/5.0'}


# --- ФУНКЦИИ ---
def get_kp_index():
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
        data = requests.get(url, headers=HEADERS, timeout=10).json()
        return float(data[-1][1])
    except:
        return None


def get_ionex_data():
    # Пробуем вчерашнюю дату, так как данные за текущие сутки могут быть не готовы
    target_date = datetime.now() - timedelta(days=1)
    day = target_date.strftime("%j")
    year = target_date.strftime("%y")
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/{target_date.year}/{day}/coDG{day}0.{year}i.gz"

    # Использование Session для сохранения авторизации
    session = requests.Session()
    session.auth = (st.secrets["EARTHDATA_USERNAME"], st.secrets["EARTHDATA_PASSWORD"])

    response = session.get(url, headers=HEADERS, timeout=30)

    if response.status_code == 200 and response.content.startswith(b'\x1f\x8b'):
        with open("data.ionex.gz", "wb") as f:
            f.write(response.content)
        return "data.ionex.gz"
    else:
        st.error(f"Ошибка загрузки (Код: {response.status_code}). Убедитесь, что логин/пароль верны.")
        return None


def parse_ionex(file_path):
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
if st.button("🚀 ЗАПУСТИТЬ МОНИТОРИНГ"):
    with st.spinner("Синхронизация..."):
        # 1. Kp-индекс
        kp = get_kp_index()
        st.metric("Глобальный Kp-индекс", kp if kp else "Нет данных")

        # 2. Ионосфера
        file_path = get_ionex_data()
        if file_path:
            grid = parse_ionex(file_path)
            # Координаты Алматы: lat 43.25, lon 76.92
            val = grid[int((43.25 + 87.5) / 2.5), int((76.92 + 180) / 5.0)]
            st.metric("VTEC над Алматы", f"{val:.2f} TECU")

        # 3. Сейсмика
        st.subheader("📉 Сейсмическая активность")
        r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&limit=10&minmagnitude=2")
        df = pd.read_csv(io.StringIO(r.text))
        st.dataframe(df[['time', 'place', 'mag']])

st.markdown("---")
st.write("Мониторинг аномалий TECU (Total Electron Content) позволяет выявлять предвестники сейсмической активности.")