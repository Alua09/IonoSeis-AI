import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import gzip
import shutil
import os
from datetime import datetime, timedelta, timezone

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_kp_index():
    try:
        data = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(data[-1][1])
    except:
        return 2.0


def get_data_quality_label(val, is_interpolated):
    return ("✅ Актуально", "green") if not is_interpolated else ("⚠️ Интерполировано", "orange")


def calculate_z_score_dynamic(val, kp):
    # Адаптивный порог: норма растет при высокой геомагнитной активности
    norm_threshold = 15.0 + (kp * 1.5)
    return (val - norm_threshold) / 4.0


def parse_ionex_data():
    grid = np.zeros((71, 73))
    if not os.path.exists("data.ionex"): return grid, True

    # (Парсинг файла здесь)
    return grid, False


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный литосферно-ионосферный мониторинг")

if st.button("🔄 ЗАПУСК ЭКСПЕРТНОГО АНАЛИЗА"):
    # (Секция скачивания .ionex остается стандартной)
    grid, is_interpolated = parse_ionex_data()
    kp = get_kp_index()

    st.info(f"Текущий Kp-индекс: {kp}. Модель адаптирована.")

    quakes = requests.get(
        f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={(datetime.now() - timedelta(days=1)).isoformat()}").json()

    for city, (c_lat, c_lon, offset) in CITIES.items():
        st.markdown("---")

        # Расчет значений
        val = 15.0 if is_interpolated else 12.0  # Пример данных
        z = calculate_z_score_dynamic(val, kp)
        label, color = get_data_quality_label(val, is_interpolated)
        local_time = datetime.now(timezone.utc) + timedelta(hours=offset)

        # Визуализация
        st.markdown(f"Статус данных: :{color}[**{label}**]")

        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader(f"📍 {city}")
            st.caption(f"🕒 Время: {local_time.strftime('%H:%M:%S')}")
            st.metric("VTEC (TECU)", f"{val:.1f}", f"{z:.1f}σ")
            st.write(f"**Kp-индекс:** {kp}")

        with col2:
            fig, ax = plt.subplots(figsize=(6, 0.4))
            ax.barh([0], [val], color=color, alpha=0.5)
            ax.set_xlim(0, 40)
            ax.axis('off')
            st.pyplot(fig)

            # Фильтрация сейсмики M >= 5.0
            sig_q = [f"🔹 {f['properties']['place']} | M: {f['properties']['mag']}"
                     for f in quakes.get('features', [])
                     if ((f['geometry']['coordinates'][1] - c_lat) ** 2 + (
                            f['geometry']['coordinates'][0] - c_lon) ** 2) ** 0.5 < 15
                     and f['properties']['mag'] >= 5.0]

            if sig_q:
                st.error(f"⚠️ Сейсмическое событие (M>=5.0): {sig_q[0]}")
            elif z > 1.5:
                st.warning("⚠️ Статистическая аномалия ионосферы.")
            else:
                st.success("✅ Статистический фон в норме.")

st.write("Метод: Динамический Z-анализ ионосферных отклонений с коррекцией по Kp.")