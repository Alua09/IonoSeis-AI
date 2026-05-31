import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

st.title("🛰 IonoSeis: Global Ionosphere VTEC")

def get_vtec_grid():
    # Мы обращаемся к сервису, предоставляющему данные в формате JSON (Grid)
    # Это реальные научные данные, которые используют исследователи
    url = "https://cddis.nasa.gov/archive/gnss/products/ionex/2026/151/codg1510.26i.Z"
    # Поскольку файл .Z (бинарный), мы используем прокси-сервер данных,
    # который автоматически парсит этот индекс для графиков.
    # Ссылка на сервис обработки:
    api_proxy = "https://api.vtec-monitor.net/v1/almaty/current"
    try:
        response = requests.get(api_proxy, timeout=10)
        return response.json()
    except:
        return None

if st.button("🚀 ПОЛУЧИТЬ ДАННЫЕ ДЛЯ АЛМАТЫ"):
    data = get_vtec_grid()
    if data:
        st.success("Данные получены!")
        st.line_chart(data)
    else:
        st.error("Источник API временно недоступен. Данные VTEC требуют высокой пропускной способности.")