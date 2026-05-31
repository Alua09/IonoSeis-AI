import streamlit as st
import pandas as pd
import xarray as xr
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI: Реальные данные")


# 1. Функция получения РЕАЛЬНЫХ данных через OPeNDAP
@st.cache_data(ttl=3600)
def get_real_vtec_data():
    # Используем URL к последним картам IGS через сервис OPeNDAP
    # Это позволяет читать данные как массив, не скачивая архивы .Z
    url = "https://cddis.nasa.gov/thredds/dodsC/ionex/2026/150/codg1500.26i.nc"
    try:
        ds = xr.open_dataset(url)
        # Извлекаем VTEC для нужной точки (индексы широты/долготы)
        vtec = ds.TEC.isel(lat=35, lon=36)  # Примерные координаты
        return vtec.to_series()
    except Exception as e:
        return None


# 2. Функция землетрясений (USGS)
def get_earthquakes():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2026-05-01&minmagnitude=4.5"
    data = requests.get(url).json()
    quakes = [{'time': pd.to_datetime(f['properties']['time'], unit='ms'), 'mag': f['properties']['mag']}
              for f in data.get('features', [])]
    return pd.DataFrame(quakes)


st.title("🛰 IonoSeis: Мониторинг на РЕАЛЬНЫХ данных NASA")

if st.button("🚀 ЗАГРУЗИТЬ ДАННЫЕ NASA"):
    with st.spinner("Подключение к серверам NASA..."):
        vtec_series = get_real_vtec_data()
        quakes = get_earthquakes()

        if vtec_series is not None:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=vtec_series.index, y=vtec_series.values, name='VTEC', line=dict(color='#00FF00')))

            # Наложение землетрясений
            for _, q in quakes.iterrows():
                fig.add_trace(go.Scatter(x=[q['time'], q['time']], y=[0, 50],
                                         mode='lines', line=dict(color='red', dash='dash'), name=f"M{q['mag']}"))

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Не удалось подключиться к серверу NASA (OPeNDAP).")