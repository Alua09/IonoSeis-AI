import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="IonoSeis AI: Анализ")
st.title("🛰 IonoSeis AI: Анализ ионосферных аномалий")

# Настройки городов
locations = {"Алматы": (43.2, 76.9), "Токио": (35.7, 139.7)}

if st.button("🚀 Запустить глубокий анализ (Май 2026)"):
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    days = np.arange(30)

    for i, (city, coords) in enumerate(locations.items()):
        # Симуляция данных VTEC (в будущем замените на парсинг IONEX)
        series = 15 + 5 * np.sin(days / 3) + np.random.normal(0, 1, 30)
        if city == "Алматы": series[5] += 12  # Имитируем аномалию

        # Симуляция Kp-индекса (Солнечная активность)
        kp_data = np.random.randint(0, 5, 30)

        # Расчет границ нормы
        mean, std = np.mean(series), np.std(series)
        upper_limit = mean + 2 * std

        # Поиск аномалий (VTEC выше нормы И Kp-индекс спокойный)
        anomalies = (series > upper_limit) & (kp_data < 4)

        # Визуализация
        ax1 = axes[i]
        ax2 = ax1.twinx()

        # VTEC (синяя линия)
        ax1.plot(days, series, color='blue', label='VTEC', linewidth=2)
        ax1.axhspan(mean - 2 * std, upper_limit, color='green', alpha=0.1, label='Норма')
        ax1.scatter(days[anomalies], series[anomalies], color='red', s=100, zorder=5,
                    label='Аномалия (Сейсмо-кандидат)')

        # Kp-индекс (желтые столбцы)
        ax2.bar(days, kp_data, color='orange', alpha=0.3, label='Kp-индекс')

        # Оформление
        ax1.set_title(f"Анализ региона: {city}")
        ax1.set_ylabel("VTEC", color='blue')
        ax2.set_ylabel("Kp-индекс", color='orange')
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')

    plt.xlabel("Дни мая 2026")
    st.pyplot(fig)
    st.success("Анализ завершен. Красные точки — подозрительные аномалии без влияния Солнца!")