import streamlit as st
import os
import matplotlib.pyplot as plt
import numpy as np
import random

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ ионосферы")

if st.button("🚀 Анализ ионосферы (Новая локация)"):
    with st.spinner("Генерация данных..."):
        # Симуляция данных без использования метода replace
        data = np.random.normal(15, 3, 500) + np.sin(np.linspace(0, 10, 500)) * 5

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.set_ylim(0, 30)
        ax.plot(data, color='#1f77b4')

        city = random.choice(['Алматы', 'Токио', 'Лондон', 'Нью-Йорк', 'Кейптаун'])
        ax.set_title(f"Данные для: {city}")

        st.pyplot(fig)
        st.success(f"Анализ завершен для: {city}")