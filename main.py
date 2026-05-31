import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="IonoSeis Pro")
st.title("🛰 IonoSeis: Геофизический мониторинг")

# Функция запроса к надежному шлюзу
def get_reliable_data():
    # GFZ Potsdam (GEOFON) — один из самых надежных в мире API для сейсмологии
    url = "https://geofon.gfz-potsdam.de/fdsnws/event/1/query?format=text&minmagnitude=4&limit=20"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Парсим текстовый ответ GFZ
            data = pd.read_csv(pd.compat.StringIO(response.text), sep='|')
            return data
        return None
    except:
        return None

if st.button("🚀 ЗАГРУЗИТЬ ДАННЫЕ GFZ"):
    df = get_reliable_data()
    if df is not None:
        st.write("События из сети GEOFON:")
        st.dataframe(df[['Time', 'Magnitude', 'RegionName']])
        st.success("Данные получены напрямую из сейсмосети GEOFON.")
    else:
        st.error("Источник GEOFON временно недоступен.")

st.info("Это не модель. Это прямые данные сейсмических станций.")