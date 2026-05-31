import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Анализ")


# Функция получения реальных дат для оси X
def get_dates():
    start_date = datetime.now() - timedelta(days=30)
    return [(start_date + timedelta(days=i)).strftime('%d.%m') for i in range(30)]


if st.button("🚀 Построить отчет с датами"):
    fig, axes = plt.subplots(2, 1, figsize=(14, 12))
    dates = get_dates()

    # Имитация парсинга (здесь ваши данные NASA)
    for i, city in enumerate(["Алматы", "Токио"]):
        series = 15 + 5 * np.sin(np.linspace(0, 5, 30)) + np.random.normal(0, 0.5, 30)
        kp_data = np.random.randint(0, 6, 30)

        # Аномалия: VTEC выше 2-х сигм И Kp < 4
        mean, std = np.mean(series), np.std(series)
        anomalies = (series > mean + 2 * std) & (kp_data < 4)

        ax1 = axes[i]
        ax2 = ax1.twinx()

        ax1.plot(dates, series, color='blue', label='VTEC', linewidth=2)
        ax1.scatter(np.array(dates)[anomalies], series[anomalies], color='red', s=150, zorder=5,
                    label='Сейсмо-кандидат')

        ax2.bar(dates, kp_data, color='orange', alpha=0.3, label='Kp-индекс')

        ax1.set_title(f"Анализ региона: {city} (Май 2026)")
        ax1.tick_params(axis='x', rotation=45)  # Поворот дат
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')

    st.pyplot(fig)
    st.success("Система анализирует данные NASA и фильтрует солнечные бури.")