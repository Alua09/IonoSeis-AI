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
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            quakes = []
            for f in data.get('features', []):
                time_val = f['properties'].get('time')
                mag_val = f['properties'].get('mag')
                if time_val and mag_val is not None:
                    quakes.append({
                        'time': pd.to_datetime(time_val, unit='ms'),
                        'mag': float(mag_val)
                    })
            return pd.DataFrame(quakes)
        return pd.DataFrame()
    except:
        return pd.DataFrame()


# 2. Функция получения данных VTEC
def get_vtec_data():
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
        if not quakes.empty:
            for _, q in quakes.iterrows():
                # Конвертация в строки заранее
                date_str = q['time'].strftime('%Y-%m-%d %H:%M:%S')
                label = "M" + str(round(q['mag'], 1))

                fig.add_vline(
                    x=date_str,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=label,
                    annotation_position="top"
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