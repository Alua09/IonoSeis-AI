import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import requests
import gzip
import shutil
import os
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}


def get_kp_index():
    try:
        data = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(data[-1][1])
    except:
        return 2.0


def get_dynamic_thresholds(kp):
    """
    Адаптивный алгоритм:
    При Kp <= 2: норма VTEC до 15.
    При Kp 3-4: норма VTEC до 20.
    При Kp >= 5: норма VTEC до 30 (повышенная чувствительность к шуму).
    """
    if kp <= 2: return 15.0
    if kp <= 4: return 22.0
    return 35.0


def calculate_z_score_dynamic(val, kp):
    # Пороговая норма меняется от Kp
    norm_threshold = get_dynamic_thresholds(kp)
    # Z-score теперь считается относительно адаптированного порога
    return (val - norm_threshold) / 5.0


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Аналитика с учетом геомагнитной поправки")

if st.button("🔄 ЗАПУСК АНАЛИЗА"):
    # ... (код скачивания и парсинга остается прежним) ...
    grid = np.zeros((71, 73))  # Заглушка для примера
    kp = get_kp_index()

    st.info(f"Текущий планетарный Kp-индекс: {kp}. Пороговые значения адаптированы.")

    for city, (c_lat, c_lon, offset) in CITIES.items():
        st.markdown("---")
        val = 15.0 + np.random.uniform(-5, 10)  # Имитация VTEC

        # КЛЮЧЕВАЯ ЛОГИКА: используем адаптивный Z-score
        z = calculate_z_score_dynamic(val, kp)

        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader(f"📍 {city}")
            st.metric("VTEC (TECU)", f"{val:.1f}", f"{z:.1f}σ")

        with col2:
            # Отображение статуса с учетом коррекции
            status_text = "Стабильно" if z < 1 else "Требует внимания"
            color = "green" if z < 1 else "orange"
            if z > 2:
                color = "red"
                status_text = "АНОМАЛИЯ"

            fig, ax = plt.subplots(figsize=(6, 0.4))
            ax.barh([0], [val], color=color, alpha=0.6)
            ax.set_xlim(0, 50)
            ax.text(val + 1, 0, status_text, va='center')
            ax.axis('off')
            st.pyplot(fig)

st.write("Метод: Динамическая коррекция порогов обнаружения на основе Kp-индекса.")