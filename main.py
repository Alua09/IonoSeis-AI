import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis AI: Сравнительный анализ аномалий")

# Настройки городов
locations = {
    "Алматы": (43.2, 76.9),
    "Токио": (35.7, 139.7)
}

if st.button("📊 Сравнить Алматы и Токио"):
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    # Генерируем данные для обоих городов (в реальности подставьте сюда чтение IONEX)
    for i, (city, coords) in enumerate(locations.items()):
        days = np.arange(30)
        # Симулируем данные (в реальности здесь будет парсинг конкретной точки из IONEX)
        series = 15 + 5 * np.sin(days / 3) + np.random.normal(0, 1, 30)

        # Добавляем искусственную аномалию для примера
        if city == "Алматы":
            series[5] += 10
        else:
            series[22] += 12

        mean, std = np.mean(series), np.std(series)
        upper = mean + 2 * std

        # График
        axes[i].plot(series, label=f'VTEC {city}', color='blue')
        axes[i].axhspan(mean - 2 * std, upper, color='green', alpha=0.2)
        axes[i].scatter(np.where(series > upper)[0], series[series > upper], color='red', s=100)
        axes[i].set_title(f"Мониторинг ионосферы: {city} {coords}")
        axes[i].set_ylabel("VTEC")
        axes[i].legend()

    plt.xlabel("Дни мая 2026")
    st.pyplot(fig)
    st.success("Сравнительный анализ готов!")