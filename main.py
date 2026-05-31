import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis: Мониторинг на данных NOAA")


@st.cache_data(ttl=600)  # Кэшируем на 10 минут
def get_real_data():
    # Используем API NOAA для K-индекса (это профессиональные данные)
    # Это НЕ модель, это реальные наблюдения геомагнитной активности
    url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
    response = requests.get(url, timeout=10)
    data = response.json()
    # Берем последние 50 записей для корректного отображения
    df = pd.DataFrame(data[1:], columns=['time', 'k_index'])
    df['time'] = pd.to_datetime(df['time'])
    df['k_index'] = df['k_index'].astype(float)
    return df.tail(50)


def get_real_earthquakes():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=4&limit=30"
    response = requests.get(url, timeout=10)
    data = response.json()
    return pd.DataFrame([
        {'time': pd.to_datetime(f['properties']['time'], unit='ms'), 'mag': f['properties']['mag']}
        for f in data.get('features', [])
    ])


if st.button("🚀 ЗАГРУЗИТЬ РЕАЛЬНЫЕ ДАННЫЕ"):
    try:
        ion = get_real_data()
        quakes = get_real_earthquakes()

        fig = go.Figure()
        # Линия реальных данных
        fig.add_trace(go.Scatter(x=ion['time'], y=ion['k_index'], name='Kp-index (NOAA)', line=dict(color='#00FF00')))

        # Сейсмические события
        for _, q in quakes.iterrows():
            fig.add_trace(go.Scatter(x=[q['time'], q['time']], y=[0, 9], mode='lines',
                                     line=dict(color='red', width=2, dash='dash'), name=f"M{q['mag']}"))

        fig.update_layout(template="plotly_dark", title="Синхронизация: Геомагнитная активность и Землетрясения")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Ошибка получения данных: {e}")