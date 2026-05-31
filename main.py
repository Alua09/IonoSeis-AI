import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime

# Пытаемся импортировать тяжелые библиотеки
try:
    import xarray as xr

    HAS_XARRAY = True
except ImportError:
    HAS_XARRAY = False

st.set_page_config(layout="wide", page_title="IonoSeis AI: Реальные данные")
st.title("🛰 IonoSeis: Мониторинг ионосферы")


def get_earthquakes():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime=2026-05-01&minmagnitude=4.5"
    try:
        data = requests.get(url, timeout=5).json()
        quakes = [{'time': pd.to_datetime(f['properties']['time'], unit='ms'), 'mag': f['properties']['mag']}
                  for f in data.get('features', [])]
        return pd.DataFrame(quakes)
    except:
        return pd.DataFrame()


if st.button("🚀 ЗАГРУЗИТЬ ДАННЫЕ"):
    if not HAS_XARRAY:
        st.error("Ошибка: Библиотека 'xarray' или 'netCDF4' не установлена. Проверьте ваш файл requirements.txt")
        st.info("Убедитесь, что в requirements.txt есть: xarray, netCDF4")
    else:
        try:
            # Реальный адрес NASA OPeNDAP (проверяем актуальный путь)
            url = "https://cddis.nasa.gov/thredds/dodsC/ionex/2026/150/codg1500.26i.nc"
            ds = xr.open_dataset(url)
            vtec = ds.TEC.isel(lat=35, lon=36).to_series()
            quakes = get_earthquakes()

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=vtec.index, y=vtec.values, name='VTEC', line=dict(color='#00FF00')))

            for _, q in quakes.iterrows():
                fig.add_trace(go.Scatter(x=[q['time'], q['time']], y=[0, 50],
                                         mode='lines', line=dict(color='red', dash='dash'), name=f"M{q['mag']}"))

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning("Сервер NASA временно недоступен по OPeNDAP. Используем имитацию для демонстрации интерфейса.")
            # Резервный вариант, чтобы вы видели график
            dates = pd.date_range(end=datetime.now(), periods=30, freq='H')
            st.line_chart(pd.DataFrame({'VTEC': np.random.uniform(10, 40, 30)}, index=dates))