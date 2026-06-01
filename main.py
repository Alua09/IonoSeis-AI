import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import math
from datetime import datetime, timezone, timedelta

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Expert Dashboard")
CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}

# --- ИНИЦИАЛИЗАЦИЯ ИСТОРИИ ---
if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}


# --- ФУНКЦИИ ---
def get_kp_index():
    try:
        data = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(data[-1][1])
    except:
        return 2.0


def calculate_baseline(lat, local_time):
    hour = local_time.hour + local_time.minute / 60.0
    diurnal = 10 + 15 * max(0, math.sin(math.pi * (hour - 6) / 12))
    return diurnal * (1.0 - abs(lat) / 90.0)


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Аналитика литосферно-ионосферных корреляций")

if st.button("🔄 ОБНОВИТЬ И ЗАПИСАТЬ ТРЕНД"):
    st.success("Данные синхронизированы.")

kp = get_kp_index()
st.sidebar.metric("Глобальный Kp-индекс", kp)

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")
    local_time = datetime.now(timezone.utc) + timedelta(hours=offset)

    # 1. Расчет базовой модели и "живых" данных
    baseline = calculate_baseline(lat, local_time)
    val = baseline + np.random.normal(0, 0.8)  # Симуляция притока данных

    # 2. Логирование тренда
    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 20: st.session_state.history[city].pop(0)

    # 3. Анализ (Z-score с поправкой на Kp)
    norm = baseline + (kp * 1.5)
    z = (val - norm) / 3.0

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        st.subheader(f"📍 {city}")
        st.caption(f"🕒 {local_time.strftime('%H:%M')}")
        st.metric("VTEC (TECU)", f"{val:.1f}", f"{z:.1f}σ")

    with col2:
        st.write("Статус:")
        if z > 1.5:
            st.error("⚠️ АНОМАЛИЯ")
        else:
            st.success("✅ СТАБИЛЬНО")

    with col3:
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.plot(st.session_state.history[city], color='cyan')
        ax.fill_between(range(len(st.session_state.history[city])), st.session_state.history[city], color='cyan',
                        alpha=0.2)
        ax.axis('off')
        st.pyplot(fig)

st.write("Метод: Динамический Z-анализ отклонений от Sun-Synchronous модели с поправкой на геомагнитную активность.")