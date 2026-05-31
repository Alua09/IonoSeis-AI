import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis: Стабильный мониторинг")


# Функция, которая создает данные БЕЗ использования опасных функций date_range
def get_demo_data():
    now = datetime.now()
    # Создаем список временных меток вручную через list comprehension
    # Это 100% будет работать на любой версии Python и Pandas
    times = [now - timedelta(hours=i) for i in range(20, 0, -1)]
    values = np.random.uniform(1, 5, 20)
    return pd.DataFrame({'time': times, 'k_index': values})


if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    try:
        # Пытаемся получить данные
        df = get_demo_data()

        # Строим график
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['time'],
            y=df['k_index'],
            mode='lines+markers',
            line=dict(color='#00CC96')
        ))

        fig.update_layout(
            template="plotly_dark",
            title="Мониторинг данных (без зависимостей от freq)"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.success("Данные успешно отображены.")

    except Exception as e:
        st.error(f"Ошибка: {e}")