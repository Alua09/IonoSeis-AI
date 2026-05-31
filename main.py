import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import re

st.set_page_config(layout="wide")
st.title("🛰 IonoSeis AI: Анализ временного ряда (Змейка)")

# Укажите координаты точки интереса (например, Алматы)
lat_target, lon_target = 43.2, 76.9

if st.button("🚀 Построить гармонический график"):
    try:
        # 1. Мы читаем данные из нескольких файлов (имитация серии)
        # В реальной работе здесь будет цикл по списку файлов IONEX
        raw_data = []
        # Допустим, мы извлекли значения TEC для конкретной точки из 30 дней:
        # Генерируем "гармонику" с шумом
        days = np.arange(30)
        base = 15 + 5 * np.sin(days / 3)  # "Змейка"
        noise = np.random.normal(0, 1, 30)
        series = base + noise

        # Вносим аномалии
        series[5] += 8
        series[20] -= 7

        # 2. Расчет границ нормы (Moving Average или Mean +/- 2*Std)
        mean = np.mean(series)
        std = np.std(series)
        upper = mean + 2 * std
        lower = mean - 2 * std

        # 3. Визуализация
        fig, ax = plt.subplots(figsize=(12, 5))

        # Рисуем "Змейку"
        ax.plot(series, color='blue', label='VTEC (TEC units)', linewidth=2)

        # Рисуем "Зеленую зону"
        ax.axhspan(lower, upper, color='green', alpha=0.2, label='Безопасная зона')

        # Рисуем "Красные точки" (аномалии)
        anomalies = (series > upper) | (series < lower)
        ax.scatter(np.where(anomalies)[0], series[anomalies], color='red', s=100, label='Аномалия', zorder=5)

        ax.set_title(f"Ионосферный мониторинг (Координаты: {lat_target}, {lon_target})")
        ax.set_xlabel("Дни")
        ax.set_ylabel("VTEC")
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)

        st.pyplot(fig)
        st.success("График готов!")

    except Exception as e:
        st.error(f"Ошибка: {e}")