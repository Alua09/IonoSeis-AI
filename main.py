import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide", page_title="IonoSeis Pro")
st.title("🛰 IonoSeis: Мониторинг на данных CODE/IGS")


# Функция получения реальных сейсмических данных (USGS)
def get_earthquakes():
    # Запрашиваем землетрясения за последние 7 дней (магнитуда 4+)
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=4&limit=50"
    response = requests.get(url, timeout=10)
    data = response.json()
    return pd.DataFrame([{'time': pd.to_datetime(f['properties']['time'], unit='ms'), 'mag': f['properties']['mag']}
                         for f in data.get('features', [])])


# Функция получения данных ионосферы через API (NOAA K-index)
def get_real_ionosphere():
    # Это реальные данные SWPC NOAA
    url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
    response = requests.get(url, timeout=10)
    data = response.json()
    df = pd.DataFrame(data[1:], columns=['time', 'k_index'])
    df['time'] = pd.to_datetime(df['time'])
    df['k_index'] = df['k_index'].astype(float)
    return df


if st.button("🚀 ЗАГРУЗИТЬ НАУЧНЫЕ ДАННЫЕ"):
    try:
        ion_data = get_real_ionosphere()
        quakes = get_earthquakes()

        fig = go.Figure()

        # 1. Линия ионосферы
        fig.add_trace(go.Scatter(x=ion_data['time'], y=ion_data['k_index'], name='K-Index (Реальный)',
                                 line=dict(color='#00FF00')))

        # 2. Линии землетрясений
        for _, q in quakes.iterrows():
            fig.add_trace(
                go.Scatter(x=[q['time'], q['time']], y=[0, 9], mode='lines', line=dict(color='red', dash='dash'),
                           name=f"M{q['mag']}"))

        fig.update_layout(template="plotly_dark", title="Синхронизированный мониторинг")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Не удалось получить данные с серверов: {e}")