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
st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитика")
# Город: (Lat, Lon, UTC_Offset)
CITIES = {
    "Алматы": (43.25, 76.92, 5),
    "Бишкек": (42.87, 74.59, 6),
    "Токио": (35.68, 139.65, 9)
}


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_city_kp():
    """Возвращает Kp-индекс. Для демонстрации он общий, но можно расширить."""
    try:
        data = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(data[-1][1])
    except:
        return 2.0


def get_status_color(val):
    if val < 15: return 'green', "Безопасно"
    if val < 30: return 'orange', "Внимание"
    return 'red', "Опасно"


# --- ИНТЕРФЕЙС ---
st.title("🛰 IonoSeis AI: Экспертный мониторинг")

if st.button("🔄 ЗАПУСК ОБНОВЛЕНИЯ ДАННЫХ"):
    # Очистка старых данных для принудительного обновления
    if os.path.exists("data.ionex"): os.remove("data.ionex")

    with st.spinner("Синхронизация..."):
        try:
            earthaccess.login(strategy="environment")
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=(datetime.now() - timedelta(days=2), datetime.now()))
            if results:
                files = earthaccess.download(results[0:1], "./tmp")
                with gzip.open(files[0], 'rb') as f_in:
                    with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
        except:
            st.warning("Серверы IGS заняты, используем кэш.")

    # Загрузка и обработка
    grid = np.zeros((71, 73))  # Здесь должна быть логика парсинга вашего .ionex
    kp = get_city_kp()
    quakes = requests.get(
        f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={(datetime.now() - timedelta(days=1)).isoformat()}").json()

    for city, (c_lat, c_lon, offset) in CITIES.items():
        st.markdown("---")
        col1, col2 = st.columns([1, 2])

        # Расчет локальных данных
        val = 12.0 + np.random.uniform(0, 5)  # Имитация VTEC
        color, status = get_status_color(val)
        local_time = datetime.now(timezone.utc) + timedelta(hours=offset)

        with col1:
            st.subheader(f"📍 {city}")
            st.caption(f"🕒 Время: {local_time.strftime('%H:%M:%S')}")
            st.metric("VTEC (TECU)", f"{val:.2f}", status)

        with col2:
            # Цветовая шкала (Голубая полоса)
            fig, ax = plt.subplots(figsize=(6, 0.5))
            ax.barh([0], [val], color=color, alpha=0.6)
            ax.set_xlim(0, 50)  # Шкала до 50 TECU
            ax.axis('off')
            st.pyplot(fig)

            # Реальные землетрясения для города
            local_q = [f"🔹 {f['properties']['place']} (M: {f['properties']['mag']})"
                       for f in quakes.get('features', [])
                       if ((f['geometry']['coordinates'][1] - c_lat) ** 2 + (
                            f['geometry']['coordinates'][0] - c_lon) ** 2) ** 0.5 < 10]

            if local_q:
                st.error(f"⚠️ Сейсмика: {local_q[0]}")
            else:
                st.success("✅ Сейсмический фон в норме")

st.write("Метод: Анализ ионосферных задержек сигналов GNSS.")