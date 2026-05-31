import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis: Стабильный мониторинг")


def get_earthquakes(lat, lon):
    url = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&latitude={lat}&longitude={lon}&maxradius=10&minmagnitude=4"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            quakes = []
            for f in data.get('features', []):
                time_val = f['properties'].get('time')
                mag_val = f['properties'].get('mag', 0)
                if time_val:
                    quakes.append({
                        'time': pd.to_datetime(time_val, unit='ms'),
                        'mag': mag_val
                    })
            return pd.DataFrame(quakes)
        return pd.DataFrame()
    except:
        return pd.DataFrame()


if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    try:
        # Данные VTEC
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        df = pd.DataFrame({'date': dates, 'vtec': np.random.uniform(15, 35, 30)})

        # Данные землетрясений
        quakes = get_earthquakes(43.2, 76.9)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['date'], y=df['vtec'], name='VTEC', line=dict(color='#00FF00')))

        # РАБОТАЕМ С ЛИНИЯМИ БЕЗ ОПЕРАЦИЙ +
        if not quakes.empty:
            for _, q in quakes.iterrows():
                # Используем форматирование f-строками (самый надежный метод)
                time_str = q['time'].strftime('%Y-%m-%d %H:%M:%S')
                mag_label = f"M{q['mag']:.1f}"

                fig.add_vline(
                    x=time_str,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=mag_label
                )

        fig.update_layout(template="plotly_dark", title="Мониторинг")
        st.plotly_chart(fig, use_container_width=True)
        st.success("Готово!")
    except Exception as e:
        # ВЫВОДИМ ТИП ОШИБКИ ДЛЯ ДИАГНОСТИКИ
        st.error(f"Тип ошибки: {type(e).__name__}. Сообщение: {e}")