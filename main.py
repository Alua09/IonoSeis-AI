import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis: Стабильный мониторинг")


# Функция получения данных о землетрясениях
def get_earthquakes(lat, lon):
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradius=10&minmagnitude=4"
    try:
        data = requests.get(url, timeout=5).json()
        quakes = [{'time': pd.to_datetime(f['properties']['time'], unit='ms'), 'mag': f['properties']['mag']}
                  for f in data.get('features', [])]
        return pd.DataFrame(quakes)
    except:
        return pd.DataFrame()


# Функция получения VTEC (имитация для примера, пока мы не подключили конкретный URL API)
def get_vtec_data():
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    # Здесь можно будет заменить на реальный запрос к API IGS
    return pd.DataFrame({'date': dates, 'vtec': np.random.uniform(15, 35, 30)})


if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    df = get_vtec_data()
    quakes = get_earthquakes(43.2, 76.9)  # Алматы

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date'], y=df['vtec'], name='VTEC Уровень', line=dict(color='green')))

    for _, q in quakes.iterrows():
        fig.add_vline(x=q['time'], line_dash="dash", line_color="red", annotation_text=f"M{q['mag']}")

    fig.update_layout(title="Мониторинг ионосферы и сейсмические события", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)