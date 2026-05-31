import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Анализ")
st.title("🛰 IonoSeis AI: Анализ ионосферных аномалий")


# Функция получения реальных землетрясений через API USGS
def get_earthquakes(lat, lon):
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "latitude": lat,
        "longitude": lon,
        "maxradius": 5,  # Радиус поиска 5 градусов (~550 км)
        "minmagnitude": 4.5,  # Порог магнитуды
        "starttime": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    }
    try:
        response = requests.get(url, params=params).json()
        # Возвращаем список дней (строки формата '05.05'), когда были землетрясения
        return [datetime.fromtimestamp(f['properties']['time'] / 1000).strftime('%d.%m')
                for f in response.get('features', [])]
    except:
        return []


locations = {"Алматы": (43.2, 76.9), "Токио": (35.7, 139.7)}

if st.button("🚀 Запустить глубокий анализ (Май 2026)"):
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    # Генерируем список дат для оси X (последние 30 дней)
    dates = [(datetime.now() - timedelta(days=30 - i)).strftime('%d.%m') for i in range(30)]

    for i, (city, coords) in enumerate(locations.items()):
        # ВАШИ ДАННЫЕ (здесь вы используете свои реальные данные из IONEX)
        series = 15 + 5 * np.sin(np.linspace(0, 5, 30)) + np.random.normal(0, 1, 30)
        kp_data = np.random.randint(0, 5, 30)

        # Получаем список дат землетрясений для региона
        quake_dates = get_earthquakes(coords[0], coords[1])

        # Расчет границ нормы
        mean, std = np.mean(series), np.std(series)
        upper_limit = mean + 2 * std
        anomalies = (series > upper_limit) & (kp_data < 4)

        # Визуализация
        ax1 = axes[i]
        ax2 = ax1.twinx()

        # VTEC (синяя линия)
        ax1.plot(dates, series, color='blue', label='VTEC', linewidth=2)
        ax1.axhspan(mean - 2 * std, upper_limit, color='green', alpha=0.1, label='Норма')
        ax1.scatter(np.array(dates)[anomalies], series[anomalies], color='red', s=100, zorder=5,
                    label='Аномалия (Сейсмо-кандидат)')

        # Наложение землетрясений (черная линия)
        for qd in quake_dates:
            if qd in dates:
                ax1.axvline(qd, color='black', linestyle='--', linewidth=2, label='Землетрясение')

        # Kp-индекс (желтые столбцы)
        ax2.bar(dates, kp_data, color='orange', alpha=0.3, label='Kp-индекс')

        # Оформление
        ax1.set_title(f"Анализ региона: {city}")
        ax1.tick_params(axis='x', rotation=45)  # Чтобы даты не накладывались
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')

    plt.tight_layout()
    st.pyplot(fig)
    st.success("Анализ завершен. Черные пунктиры — факты землетрясений, красные точки — потенциальные предвестники.")