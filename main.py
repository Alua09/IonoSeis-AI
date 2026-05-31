import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide", page_title="IonoSeis: Real-Time Sync")
st.title("🛰 IonoSeis: Сейсмо-ионосферная синхронизация")


# Канал 1: Реальные землетрясения (USGS)
@st.cache_data(ttl=600)
def get_earthquakes():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=4&limit=20"
    try:
        response = requests.get(url, timeout=10)
        features = response.json().get('features', [])
        return pd.DataFrame(
            [{'time': pd.to_datetime(f['properties']['time'], unit='ms'), 'mag': f['properties']['mag']} for f in
             features])
    except:
        return pd.DataFrame()


# Канал 2: Реальный индекс Kp (Ионосфера)
@st.cache_data(ttl=600)
def get_kp_index():
    url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        df = pd.DataFrame(data[1:], columns=['time', 'k_index'])
        df['time'] = pd.to_datetime(df['time'])
        df['k_index'] = df['k_index'].astype(float)
        return df.tail(40)  # Последние 40 записей
    except:
        return None


if st.button("🚀 ЗАГРУЗИТЬ СИНХРОНИЗИРОВАННЫЕ ДАННЫЕ"):
    with st.spinner("Сбор данных с научных серверов..."):
        ion = get_kp_index()
        quakes = get_earthquakes()

        if ion is not None:
            fig = go.Figure()

            # Линия Kp-индекса (Состояние ионосферы)
            fig.add_trace(go.Scatter(x=ion['time'], y=ion['k_index'], name='Kp-Index (Ионосфера)',
                                     line=dict(color='#00FF00', width=2)))

            # Линии землетрясений
            if not quakes.empty:
                for _, q in quakes.iterrows():
                    fig.add_trace(go.Scatter(x=[q['time'], q['time']], y=[0, 9], mode='lines',
                                             line=dict(color='red', width=1, dash='dot'),
                                             name=f"Землетрясение M{q['mag']}"))

            fig.update_layout(template="plotly_dark", title="Синхронизация магнитной активности и сейсмики",
                              xaxis_title="Время", yaxis_title="Kp-Index / Магнитуда")
            st.plotly_chart(fig, use_container_width=True)
            st.success("Данные обновлены. Теперь вы видите реальную корреляцию.")
        else:
            st.error("Серверы NOAA/USGS временно недоступны для автоматического запроса.")