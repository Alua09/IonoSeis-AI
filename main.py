import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis: Стабильный мониторинг")


# Функция получения землетрясений (USGS)
def get_earthquakes(lat, lon):
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradius=10&minmagnitude=4"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame([
                {'time': pd.to_datetime(f['properties']['time'], unit='ms'), 'mag': float(f['properties']['mag'])}
                for f in data.get('features', [])
            ])
    except:
        pass
    return pd.DataFrame(columns=['time', 'mag'])


# Функция получения K-индекса с двойной защитой
def get_k_index():
    # Попытка 1: NOAA
    try:
        url = "https://services.swpc.noaa.gov/products/noaa-k-index.json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data[1:], columns=['time', 'k_index'])
    except:
        pass

    # Попытка 2 (если NOAA упал): Возвращаем пустой объект, но не ломаем приложение
    return pd.DataFrame(columns=['time', 'k_index'])


# Основная логика
if st.button("🚀 ЗАГРУЗИТЬ ДАННЫЕ"):
    with st.spinner("Запрос к серверам..."):
        ion_df = get_k_index()
        quakes = get_earthquakes(43.2, 76.9)

        if ion_df.empty:
            st.error("Серверы данных временно недоступны. Попробуйте нажать кнопку еще раз через минуту.")
        else:
            # Преобразование форматов
            ion_df['time'] = pd.to_datetime(ion_df['time'])
            ion_df['k_index'] = ion_df['k_index'].astype(float)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ion_df['time'], y=ion_df['k_index'], name='K-Index', line=dict(color='#00CC96')))

            # Линии событий
            for _, q in quakes.iterrows():
                fig.add_trace(go.Scatter(x=[q['time'], q['time']], y=[0, 9], mode='lines',
                                         line=dict(color='red', dash='dash'), name=f"M{q['mag']}"))

            fig.update_layout(template="plotly_dark", title="Мониторинг K-Index и землетрясений")
            st.plotly_chart(fig, use_container_width=True)
            st.success("Данные успешно загружены.")

st.info(
    "Техническая справка: Если данные не грузятся, значит API NOAA на техобслуживании. Это происходит редко, но бывает.")