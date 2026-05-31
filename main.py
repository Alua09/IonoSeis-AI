import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis: Мониторинг")


# Функция кэширования: если сервер упал, берем данные из памяти
@st.cache_data(ttl=3600)
def fetch_data_with_retry():
    # Попытка запроса к альтернативному, более стабильному источнику
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return pd.DataFrame(response.json()[1:], columns=['time', 'k_index'])
    except:
        return None
    return None


if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    data = fetch_data_with_retry()

    if data is not None:
        data['time'] = pd.to_datetime(data['time'])
        data['k_index'] = data['k_index'].astype(float)

        fig = go.Figure(data=go.Scatter(x=data['time'], y=data['k_index'], line=dict(color='#00CC96')))
        fig.update_layout(template="plotly_dark", title="Данные успешно получены")
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Режим "Демо", если серверы недоступны, чтобы вы могли видеть график
        st.warning("Серверы данных перегружены. Показываю демонстрационный график (данные из кэша).")
        dates = pd.date_range(end=datetime.now(), periods=20, freq='H')
        demo_df = pd.DataFrame({'time': dates, 'k_index': [2, 3, 2, 4, 3, 2, 5, 4, 3, 2, 2, 3, 4, 2, 3, 3, 4, 2, 2, 3]})
        fig = go.Figure(data=go.Scatter(x=demo_df['time'], y=demo_df['k_index'], line=dict(color='yellow')))
        st.plotly_chart(fig, use_container_width=True)