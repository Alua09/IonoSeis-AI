import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis: Мониторинг сейсмической активности")


# 1. СЕЙСМИЧЕСКИЕ ДАННЫЕ (Стабильно работают)
def get_earthquakes():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=4&limit=20"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            features = response.json().get('features', [])
            return pd.DataFrame([
                {'time': pd.to_datetime(f['properties']['time'], unit='ms'), 'mag': f['properties']['mag']}
                for f in features
            ])
    except:
        return pd.DataFrame()
    return pd.DataFrame()


# 2. ИОНОСФЕРНЫЕ ДАННЫЕ (Упрощенный расчет VTEC для теста)
def get_ionosphere_mock():
    # Генерируем данные на основе синусоиды, чтобы график всегда строился
    # Это гарантирует, что приложение не упадет из-за отсутствия API NASA
    hours = np.linspace(0, 24, 24)
    vtec = 25 + 10 * np.sin(hours * np.pi / 12) + np.random.normal(0, 1, 24)
    times = [datetime.now().replace(hour=int(h), minute=0) for h in hours]
    return pd.DataFrame({'time': times, 'vtec': vtec})


if st.button("🚀 ЗАГРУЗИТЬ"):
    df_ion = get_ionosphere_mock()
    df_quake = get_earthquakes()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_ion['time'], y=df_ion['vtec'], name='VTEC (Model)', line=dict(color='#00FF00')))

    for _, q in df_quake.iterrows():
        fig.add_trace(
            go.Scatter(x=[q['time'], q['time']], y=[0, 40], mode='lines', line=dict(color='red', dash='dash')))

    fig.update_layout(template="plotly_dark", title="Мониторинг активности")
    st.plotly_chart(fig, use_container_width=True)
    st.success("Интерфейс активен. Используются данные USGS для сейсмики.")