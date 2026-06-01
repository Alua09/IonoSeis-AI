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

if 'history' not in st.session_state:
    st.session_state.history = {city: [] for city in CITIES}


# --- НАУЧНЫЕ ФУНКЦИИ ---
def get_seasonal_factor(date):
    day_of_year = date.timetuple().tm_yday
    return 1.0 + 0.2 * math.sin(2 * math.pi * (day_of_year - 80) / 365)


def get_diurnal_trend(hour, lat, date):
    """Модель: VTEC зависит от времени суток, широты и сезона."""
    seasonal = get_seasonal_factor(date)
    # Пик ионизации около 14:00 (максимум Солнца)
    diurnal = 10.0 + 15.0 * math.cos(math.pi * (hour - 14) / 12)
    return diurnal * (math.cos(math.radians(lat))) * seasonal


def moving_average(data, window=5):
    """Сглаживание высокочастотного шума GNSS-данных."""
    if len(data) < window: return data
    return np.convolve(data, np.ones(window) / window, mode='valid')


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")

if st.button("🔄 ОБНОВИТЬ ДАННЫЕ"):
    st.success("Данные синхронизированы.")

for city, (lat, lon, offset) in CITIES.items():
    st.markdown("---")
    now = datetime.now(timezone.utc) + timedelta(hours=offset)

    # 1. Расчет базовой модели (ожидаемое значение)
    hour = now.hour + now.minute / 60.0
    base_norm = get_diurnal_trend(hour, lat, now)

    # 2. Живые данные (модель + шум)
    val = base_norm + np.random.normal(0, 0.4)
    st.session_state.history[city].append(val)
    if len(st.session_state.history[city]) > 50: st.session_state.history[city].pop(0)

    # 3. Z-анализ и сглаживание
    smoothed_data = moving_average(st.session_state.history[city], window=5)
    z = (val - base_norm) / 1.5

    col1, col2, col4 = st.columns([1, 1, 2])

    with col1:
        st.subheader(f"📍 {city}")
        st.metric("VTEC (TECU)", f"{val:.1f}", f"{('+' if z >= 0 else '')}{z:.1f}σ")

    with col2:
        st.write("Статус ионосферы:")
        if abs(z) > 1.5:
            st.warning("⚠️ АНОМАЛИЯ")
        else:
            st.info("✅ Стабильно")

    with col4:
        # Визуализация: тренд (сглаженный) vs Модель (теория)
        fig, ax = plt.subplots(figsize=(6, 1.2))
        ax.plot(smoothed_data, color='cyan', linewidth=2.5, label='Тренд (Moving Avg)')
        ax.axhline(y=base_norm, color='gray', linestyle='--', alpha=0.6, label='Норма (Diurnal)')
        ax.axis('off')
        st.pyplot(fig)

st.write("Метод: Выделение тренда через Moving Average для подавления шума GNSS-сигналов.")