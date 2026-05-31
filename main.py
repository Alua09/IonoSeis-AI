import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis: Мониторинг")


def get_earthquakes():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=4&limit=20"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            features = response.json().get('features', [])
            return pd.DataFrame([
                {'time': pd.to_datetime(f['properties']['time'], unit='ms'), 'mag': f['properties']['mag']}
                for f in features
            ])
    except:
        return pd.DataFrame(columns=['time', 'mag'])
    return pd.DataFrame(columns=['time', 'mag'])


def get_ionosphere_mock():
    # Генерируем ровно 24 точки (часа), от 0 до 23
    hours = np.arange(24)
    vtec = 25 + 10 * np.sin(hours * np.pi / 12) + np.random.normal(0, 1, 24)
    now = datetime.now()
    times = [now.replace(hour=int(h), minute=0, second=0, microsecond=0) for h in hours]
    return pd.DataFrame({'time': times, 'vtec': vtec})


if st.button("🚀 ЗАГРУЗИТЬ"):
    try:
        df_ion = get_ionosphere_mock()
        df_quake = get_earthquakes()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_ion['time'], y=df_ion['vtec'], name='VTEC (Model)', line=dict(color='#00FF00')))

        if not df_quake.empty:
            for _, q in df_quake.iterrows():
                fig.add_trace(go.Scatter(x=[q['time'], q['time']], y=[0, 40], mode='lines',
                                         line=dict(color='red', dash='dash'), name=f"M{q['mag']}"))

        fig.update_layout(template="plotly_dark", title="Мониторинг активности")
        st.plotly_chart(fig, use_container_width=True)
        st.success("Данные успешно загружены.")
    except Exception as e:
        st.error(f"Произошла ошибка при отрисовке: {e}")