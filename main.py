import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide", page_title="IonoSeis AI: Полная автоматизация")
st.title("🛰 IonoSeis: Автоматический мониторинг")


# Функция для получения данных из стабильных API (без авторизации)
def fetch_data_automated():
    try:
        # API индекса солнечной активности (стабильный прокси-сервер)
        url = "https://services.swpc.noaa.gov/json/solar_cycle/observed_flux_values.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Берем последние 30 значений
            df = pd.DataFrame(data[-30:])
            return df
        return None
    except:
        return None


if st.button("🚀 ЗАГРУЗИТЬ АВТОМАТИЧЕСКИ"):
    with st.spinner("Синхронизация с серверами..."):
        df = fetch_data_automated()

        if df is not None:
            fig = go.Figure()
            # Отрисовка данных Flux (индекс ионосферного воздействия)
            fig.add_trace(
                go.Scatter(x=df['time-tag'], y=df['flux'], name='Solar Flux Index', line=dict(color='#00FF00')))

            fig.update_layout(
                template="plotly_dark",
                title="Автоматический мониторинг солнечного потока",
                xaxis_title="Дата",
                yaxis_title="Flux Index"
            )
            st.plotly_chart(fig, use_container_width=True)
            st.success("Данные обновлены в автоматическом режиме.")
        else:
            st.error("В данный момент серверы API недоступны для автоматической синхронизации.")

st.info(
    "Работает полностью автоматически. Мы переключились на Solar Flux Index — это ключевой параметр, определяющий состояние ионосферы.")