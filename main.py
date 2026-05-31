import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis: Стабильный мониторинг")


# Генерация данных без ошибок частоты
def get_safe_data():
    now = datetime.now()
    # Генерируем даты как список объектов datetime, чтобы избежать проблем с freq
    dates = [now - timedelta(hours=i) for i in range(30, 0, -1)]
    vtec = np.random.uniform(15, 35, 30)
    return pd.DataFrame({'date': dates, 'vtec': vtec})


if st.button("🚀 ЗАГРУЗИТЬ ДАННЫЕ"):
    try:
        df = get_safe_data()

        # Используем Plotly Express для графиков - это в 10 раз надежнее
        # Он сам понимает типы данных и не требует ручных линий
        fig = px.line(df, x='date', y='vtec', title="Мониторинг VTEC (Live Demo)")
        fig.update_traces(line_color='#00FF00')
        fig.update_layout(template="plotly_dark")

        st.plotly_chart(fig, use_container_width=True)
        st.success("Данные отображены!")

    except Exception as e:
        st.error(f"Критическая ошибка: {e}")