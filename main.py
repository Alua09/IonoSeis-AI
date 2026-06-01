import streamlit as st
import requests
import gzip
import shutil
import numpy as np
import pandas as pd
import io
from datetime import datetime

st.set_page_config(layout="wide", page_title="IonoSeis AI: Pro Monitor")
st.title("🛰 IonoSeis AI: Мониторинг литосферно-ионосферной связи")

# --- КОНФИГУРАЦИЯ ---
ALMATY_LAT, ALMATY_LON = 43.25, 76.92
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
    now = datetime.now()
    day = now.strftime("%j")
    year = now.strftime("%y")
    # Ссылка на архив CDDIS NASA
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/{now.year}/{day}/coDG{day}0.{year}i.gz"

    # Авторизация через ваши Secrets
    auth = (st.secrets["EARTHDATA_USERNAME"], st.secrets["EARTHDATA_PASSWORD"])
    response = requests.get(url, auth=auth, headers=HEADERS, timeout=20)

    if response.status_code == 200:
        with open("data.ionex.gz", 'wb') as f: f.write(response.content)
        return "data.ionex.gz"
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
    with st.spinner("Синхронизация с NASA и NOAA..."):
        # 1. Kp-индекс
        kp = get_kp_index()
        st.metric("Глобальный Kp-индекс", kp if kp else "Нет данных")

        # 2. Ионосфера
        file_path = get_ionex_data()
        if file_path:
            grid = parse_ionex(file_path)
            val = grid[int((ALMATY_LAT + 87.5) / 2.5), int((ALMATY_LON + 180) / 5.0)]
            st.metric("VTEC над Алматы", f"{val:.2f} TECU")
        else:
            st.warning("Данные ионосферы NASA недоступны.")

        # 3. Сейсмика
        st.subheader("📉 Сейсмическая активность (USGS)")
        r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&limit=10&minmagnitude=2")
        df = pd.read_csv(io.StringIO(r.text))
        st.dataframe(df[['time', 'place', 'mag']])

st.markdown("---")
st.write(
    "Механизм мониторинга основан на анализе электронов в ионосфере (VTEC) и корреляции с геомагнитной активностью (Kp).")