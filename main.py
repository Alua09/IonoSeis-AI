import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from io import StringIO

st.set_page_config(layout="wide", page_title="IonoSeis: Автономный монитор")
st.title("🛰 IonoSeis: Мульти-источниковый сейсмо-монитор")


# Функция с перебором нескольких источников (Fallbacks)
def get_seismic_data():
    sources = [
        "https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&minmagnitude=4",
        "https://geofon.gfz-potsdam.de/fdsnws/event/1/query?format=text&minmagnitude=4"
    ]

    for url in sources:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                # Универсальная обработка CSV/Text формата
                data = pd.read_csv(StringIO(response.text))
                return data, url
        except:
            continue
    return None, None


if st.button("🚀 ЗАГРУЗИТЬ ДАННЫЕ (АВТО-ВЫБОР ИСТОЧНИКА)"):
    with st.spinner("Поиск доступных сейсмо-станций..."):
        df, source = get_seismic_data()

        if df is not None:
            st.success(f"Данные успешно получены из: {source}")
            st.dataframe(df.head(10))

            # Отрисовка
            fig = go.Figure()
            # Предполагаем колонки Time и Magnitude (стандарт USGS/GFZ)
            fig.add_trace(go.Scatter(x=df.iloc[:, 0], y=df.iloc[:, 4], mode='markers'))
            fig.update_layout(template="plotly_dark", title="События в реальном времени")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Все сейсмические шлюзы временно недоступны. Это критический сбой сети.")