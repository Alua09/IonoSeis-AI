import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide", page_title="IonoSeis Pro")
st.title("🛰 IonoSeis: Мониторинг")


def get_data_safe(url):
    try:
        response = requests.get(url, timeout=10)
        # Проверяем, что ответ не пустой и это JSON
        if response.status_code == 200 and response.text.strip():
            return response.json()
    except:
        pass
    return None


if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    with st.spinner("Запрос к серверам..."):
        data = get_data_safe("https://services.swpc.noaa.gov/products/noaa-k-index.json")

        if data:
            try:
                df = pd.DataFrame(data[1:], columns=['time', 'k_index'])
                df['time'] = pd.to_datetime(df['time'])
                df['k_index'] = df['k_index'].astype(float)

                fig = go.Figure(data=go.Scatter(x=df['time'], y=df['k_index'], line=dict(color='#00FF00')))
                fig.update_layout(template="plotly_dark", title="Данные успешно получены")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Ошибка обработки данных: {e}")
        else:
            st.warning(
                "Сервер NOAA вернул пустой ответ. Попробуйте обновить страницу через пару минут — это стандартное поведение API при перегрузках.")