import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis: Стабильный мониторинг ионосферы")


# 1. Функция получения землетрясений
def get_earthquakes(lat, lon):
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradius=10&minmagnitude=4"
    try:
        data = requests.get(url, timeout=5).json()
        quakes = [{'time': pd.to_datetime(f['properties']['time'], unit='ms'), 'mag': f['properties']['mag']}
                  for f in data.get('features', [])]
        return pd.DataFrame(quakes)
    except:
        return pd.DataFrame()


# 2. Функция получения VTEC (структура данных)
def get_vtec_data():
    # Генерируем временной ряд для демонстрации стабильности
    # В будущем сюда добавится API IGS
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    return pd.DataFrame({'date': dates, 'vtec': np.random.uniform(15, 35, 30)})


# 3. Основная логика
if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    try:
        df = get_vtec_data()
        quakes = get_earthquakes(43.2, 76.9)  # Алматы

        fig = go.Figure()

        # Линия VTEC
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['vtec'],
            name='VTEC Уровень',
            line=dict(color='#00FF00', width=2)
        ))

        # Красные линии землетрясений
        for _, q in quakes.iterrows():
            time_str = q['time'].strftime('%Y-%m-%d %H:%M:%S')
            fig.add_vline(
                x=time_str,
                line_dash="dash",
                line_color="red",
                annotation_text=f"M{q['mag']}"
            )

        fig.update_layout(
            title="Динамика ионосферы и сейсмические события",
            template="plotly_dark",
            xaxis_title="Дата",
            yaxis_title="VTEC Units"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.success("Данные успешно обновлены!")

    except Exception as e:
        st.error(f"Ошибка при построении графика: {e}")