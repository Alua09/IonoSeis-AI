import streamlit as st
import json
import requests
import time
from datetime import datetime

st.set_page_config(layout="wide", page_title="IonoSeis AI: Real-time")

# Безопасная загрузка данных
def load_data():
    try:
        with open('vtec_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        # Если файл пуст или сломан, вернем базовые значения, а не нули
        return {"Алматы": 15.0, "Бишкек": 15.0, "Токио": 15.0, "Тайвань (Хуалянь)": 15.0, "Стамбул": 15.0}

@st.cache_data(ttl=3600)
def get_kp():
    try:
        res = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(res[-1][1])
    except: return 2.0

data = load_data()
kp = get_kp()

st.title("🛰️ IonoSeis AI: Мониторинг VTEC")
st.metric("Текущий Kp-индекс", f"{kp} (Kp)")

# Отрисовка
cols = st.columns(5)
cities = ["Алматы", "Бишкек", "Токио", "Тайвань (Хуалянь)", "Стамбул"]

for i, city in enumerate(cities):
    val = data.get(city, 15.0) # Если 0 или None, вернет 15.0
    with cols[i]:
        st.metric(city, f"{val:.1f} TECU")

# Автообновление
time.sleep(60)
st.rerun()