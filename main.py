import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="IonoSeis AI: Анализ")
st.title("🛰 IonoSeis AI: Совмещенный анализ VTEC и Kp")

locations = {"Алматы": (43.2, 76.9), "Токио": (35.7, 139.7)}

if st.button("🚀 Построить совмещенные графики"):
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    days = np.arange(30)

    for i, (city, coords) in enumerate(locations.items()):
        # Симуляция VTEC (замените на парсинг IONEX)
        series = 15 + 5 * np.sin(days / 3) + np.random.normal(0, 1, 30)
        if city == "Алматы": series[5] += 12

        # Симуляция Kp-индекса
        kp_data = np.random.randint(0, 5, 30)

        # Создаем две оси для одного города (одна для VTEC, вторая для Kp)
        ax1 = axes[i]
        ax2 = ax1.twinx()

        # VTEC (синяя линия)
        ax1.plot(days, series, color='blue', label='VTEC', linewidth=2)
        ax1.axhspan(np.mean(series) - 2 * np.std(series), np.mean(series) + 2 * np.std(series),
                    color='green', alpha=0.1, label='Норма VTEC')

        # Kp-индекс (желтые столбцы)
        ax2.bar(days, kp_data, color='orange', alpha=0.3, label='Kp-индекс')

        # Оформление
        ax1.set_title(f"Анализ: {city}")
        ax1.set_ylabel("VTEC", color='blue')
        ax2.set_ylabel("Kp-индекс", color='orange')

        # Легенда
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper left')

    plt.xlabel("Дни мая 2026")
    st.pyplot(fig)