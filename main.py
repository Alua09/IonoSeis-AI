import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Настройки страницы
st.set_page_config(layout="wide", page_title="IonoSeis AI: Аналитический комплекс")
st.title("🛰 IonoSeis AI: Мониторинг и прогноз")

locations = {"Алматы": (43.2, 76.9), "Токио": (35.7, 139.7)}


def get_data_for_region(coords):
    # Здесь в будущем будет вызов парсера IONEX (через earthaccess)
    # Сейчас имитируем реальные данные для демонстрации
    days = np.arange(30)
    series = 15 + 5 * np.sin(days / 3) + np.random.normal(0, 0.5, 30)
    kp_data = np.random.randint(0, 6, 30)
    return days, series, kp_data


if st.button("🚀 Анализ данных"):
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))

    for i, (city, coords) in enumerate(locations.items()):
        days, series, kp_data = get_data_for_region(coords)

        # Расчет нормы
        mean, std = np.mean(series), np.std(series)
        upper_limit = mean + 2 * std

        # Аномалия = VTEC выше нормы И отсутствие солнечной бури (Kp < 4)
        anomalies = (series > upper_limit) & (kp_data < 4)

        # Графики
        ax1 = axes[i]
        ax2 = ax1.twinx()

        # VTEC (синяя линия)
        ax1.plot(days, series, color='blue', label='VTEC', linewidth=2)
        ax1.axhspan(mean - 2 * std, upper_limit, color='green', alpha=0.1, label='Норма')
        ax1.scatter(days[anomalies], series[anomalies], color='red', s=100, label='Сейсмо-аномалия', zorder=5)

        # Kp-индекс (желтые столбцы)
        ax2.bar(days, kp_data, color='orange', alpha=0.3, label='Kp-индекс (Солнце)')

        ax1.set_title(f"Регион: {city}")
        ax1.set_ylabel("VTEC (Total Electron Content)", color='blue')
        ax2.set_ylabel("Kp-индекс", color='orange')
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')

    st.pyplot(fig)
    st.markdown("""
    **Расшифровка графиков:**
    - **Синяя линия**: Изменение электронной плотности (VTEC).
    - **Зеленый коридор**: Нормальный фон ионосферы.
    - **Красные точки**: Сейсмические кандидаты (аномалии при спокойном Солнце).
    - **Желтые столбцы**: Индекс солнечной активности (Kp).
    """)