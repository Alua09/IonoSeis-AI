import streamlit as st
import requests
import gzip
import shutil
import numpy as np
import pandas as pd
import io
import os
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Final")
st.title("🛰 IonoSeis AI: Мониторинг геофизических аномалий")


# --- ФУНКЦИИ ---
def get_kp_index():
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
        data = requests.get(url, timeout=5).json()
        return float(data[-1][1])
    except:
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


def get_ionex_data():
    # 1. Попытка скачать свежий файл
    now = datetime.now()
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/{now.year}/{now.strftime('%j')}/coDG{now.strftime('%j')}0.{now.strftime('%y')}i.gz"

    try:
        session = requests.Session()
        session.auth = (st.secrets["EARTHDATA_USERNAME"], st.secrets["EARTHDATA_PASSWORD"])
        response = session.get(url, timeout=10)
        if response.status_code == 200 and response.content.startswith(b'\x1f\x8b'):
            with open("live_data.gz", "wb") as f: f.write(response.content)
            return "live_data.gz"
    except:
        pass

    # 2. Если не вышло — берем резервный файл из GitHub-репозитория
    if os.path.exists("backup_ionex.gz"):
        return "backup_ionex.gz"
    return None


# --- ИНТЕРФЕЙС ---
if st.button("🚀 ЗАПУСТИТЬ МОНИТОРИНГ"):
    with st.spinner("Синхронизация с базами данных..."):
        # Ионосфера
        file_path = get_ionex_data()
        if file_path:
            grid = parse_ionex(file_path)
            val = grid[int((43.25 + 87.5) / 2.5), int((76.92 + 180) / 5.0)]
            st.metric("VTEC над Алматы", f"{val:.2f} TECU")

        # Kp-индекс и Сейсмика
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Глобальный Kp-индекс", get_kp_index() or "N/A")

        with col2:
            st.subheader("Сейсмика (USGS)")
            r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&limit=5&minmagnitude=2")
            df = pd.read_csv(io.StringIO(r.text))
            st.dataframe(df[['place', 'mag']])

st.markdown("---")
st.write("Связь литосферы и ионосферы основана на изменении плотности электронов перед тектоническими сдвигами.")