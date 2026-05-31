import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="IonoSeis AI: Анализ")
st.title("🛰 IonoSeis AI: Мониторинг ионосферы и Kp-индекс")

# Координаты
locations = {"Алматы": (43.2, 76.9), "Токио": (35.7, 139.7)}

if st.button("🚀 Анализ данных"):
    # Генерируем два графика друг под другом
    fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
    days = np.arange(30)

    # 1 и 2. Графики для городов
    for i, (city, coords) in enumerate(locations.items()):
        # Симуляция VTEC (замените на парсинг IONEX)
        series = 15 + 5 * np.sin(days / 3) + np.random.normal(0, 1, 30)
        if city == "Алматы": series[5] += 12  # Имитация аномалии

        mean, std = np.mean(series), np.std(series)
        axes[i].plot(series, label=f'VTEC {city}', color='blue')
        axes[i].axhspan(mean - 2 * std, mean + 2 * std, color='green', alpha=0.2)
        axes[i].scatter(np.where(series > mean + 2 * std)[0], series[series > mean + 2 * std], color='red', s=100)
        axes[i].set_ylabel("VTEC")
        axes[i].legend()

    # 3. Kp-индекс (магнитосферная возмущенность)
    kp_data = np.random.randint(0, 5, 30)  # Kp от 0 до 9
    axes[2].bar(days, kp_data, color='orange', label='Kp-индекс (солнечная активность)')
    axes[2].axhline(4, color='red', linestyle='--', label='Критический порог (Буря)')
    axes[2].set_ylabel("Kp-индекс")
    axes[2].legend()
    axes[2].set_xlabel("Дни мая 2026")

    st.pyplot(fig)
    st.markdown("""
    **Как читать графики:**
    - Если **красная точка** на VTEC совпадает с **высоким Kp-индексом** (выше 4) — это эффект солнечной бури (не сейсмика).
    - Если **красная точка** есть, а Kp-индекс низкий — это **потенциально сейсмический сигнал**.
    """)