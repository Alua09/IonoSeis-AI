import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="IonoSeis AI: Прогноз")
st.title("🛰 IonoSeis AI: Прогноз и мониторинг")


# Функция прогноза (простой тренд + сезонность)
def get_forecast(data):
    # Скользящее среднее как базовый прогноз на следующий день
    return np.mean(data[-5:])


if st.button("🚀 Анализ реальных данных + Прогноз"):
    fig, ax = plt.subplots(figsize=(12, 6))

    # Имитация исторических данных (здесь будет ваш реальный парсинг IONEX)
    real_data = 15 + 5 * np.sin(np.linspace(0, 10, 30))

    # Прогноз на завтра
    forecast = get_forecast(real_data)

    # Отрисовка
    ax.plot(real_data, label='История VTEC', color='blue')
    ax.axhline(forecast, color='red', linestyle='--', label=f'Прогноз на завтра: {forecast:.2f}')

    # Добавляем "Коридор нормы"
    ax.fill_between(range(31), forecast - 2, forecast + 2, color='green', alpha=0.1)

    ax.set_title("Мониторинг с авто-прогнозированием")
    ax.legend()
    st.pyplot(fig)

    st.write(f"### Статус: {'СПОКОЙНО' if abs(real_data[-1] - forecast) < 2 else 'АНОМАЛИЯ'}")