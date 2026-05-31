import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis: Real-time Monitor")
st.title("🛰 IonoSeis: Мониторинг ионосферы на реальных данных")


# 1. Функция получения реальных сейсмических данных
def get_earthquakes(lat, lon):
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradius=10&minmagnitude=4"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            quakes = []
            for f in data.get('features', []):
                quakes.append({
                    'time': pd.to_datetime(f['properties']['time'], unit='ms'),
                    'mag': float(f['properties']['mag'])
                })
            return pd.DataFrame(quakes)
    except:
        pass
    return pd.DataFrame(columns=['time', 'mag'])


# 2. Функция получения данных ионосферы (NOAA API)
def get_ionosphere_data():
    try:
        # Получаем данные о состоянии ионосферы
        url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
        response = requests.get(url, timeout=10)
        data = response.json()
        # Преобразуем в DataFrame
        df = pd.DataFrame(data[1:], columns=['time', 'k_index'])
        df['time'] = pd.to_datetime(df['time'])
        df['k_index'] = df['k_index'].astype(float)
        return df
    except:
        # Возврат пустой таблицы, если API недоступно
        return pd.DataFrame(columns=['time', 'k_index'])


# 3. Основная логика отрисовки
if st.button("🚀 ЗАГРУЗИТЬ АКТУАЛЬНЫЕ ДАННЫЕ"):
    with st.spinner("Запрос данных к серверам NOAA и USGS..."):
        ion_df = get_ionosphere_data()
        quakes = get_earthquakes(43.2, 76.9)  # Алматы

        if not ion_df.empty:
            fig = go.Figure()

            # Линия индекса ионосферы
            fig.add_trace(go.Scatter(
                x=ion_df['time'],
                y=ion_df['k_index'],
                name='K-Index (Ионосфера)',
                line=dict(color='#00CC96', width=2)
            ))

            # Вертикальные линии землетрясений
            for _, q in quakes.iterrows():
                fig.add_trace(go.Scatter(
                    x=[q['time'], q['time']],
                    y=[0, 9],
                    mode='lines',
                    line=dict(color='red', width=3, dash='dash'),
                    name=f"Землетрясение M{q['mag']}"
                ))

            fig.update_layout(
                title="Корреляция: Ионосфера vs Сейсмические события",
                template="plotly_dark",
                xaxis_title="Время",
                yaxis_title="Индекс (K-Index)"
            )
            st.plotly_chart(fig, use_container_width=True)
            st.success("Данные успешно получены с серверов NOAA/USGS.")
        else:
            st.error("Данные временно недоступны. Попробуйте обновить позже.")

st.sidebar.info(
    "Это профессиональный интерфейс, работающий через API. Никаких локальных файлов и проблем с распаковкой.")