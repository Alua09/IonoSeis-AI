import streamlit as st
import pandas as pd
import plotly.express as px
import data_pipeline

st.set_page_config(page_title="IonoSeis AI", layout="wide")

st.title("🛰 IonoSeis: Интеллектуальный мониторинг ионосферы")

# Кнопка для живого обновления данных
if st.button("🔄 Обновить данные в реальном времени"):
    data_pipeline.get_latest_ionosphere_data()

# Загрузка и анализ
try:
    df = pd.read_csv("live_data.csv")

    st.header("Аналитика по станциям")

    # Визуализация и Светофор
    cols = st.columns(len(df))
    for i, row in df.iterrows():
        vtec = row['VTEC']
        # Логика светофора
        if vtec < 18:
            status, color = "Норма", "success"
        elif 18 <= vtec < 23:
            status, color = "Повышенный уровень", "warning"
        else:
            status, color = "Аномалия", "error"

        with cols[i]:
            st.metric(f"Станция {row['Station']}", f"{vtec:.1f} TECU")
            if color == "success":
                st.success(status)
            elif color == "warning":
                st.warning(status)
            else:
                st.error(status)

    # График
    fig = px.bar(df, x='Station', y='VTEC', color='VTEC',
                 color_continuous_scale='RdYlGn_r', title="Уровень ионизации (VTEC)")
    st.plotly_chart(fig, use_container_width=True)

    # Вывод для анализа
    if df['VTEC'].max() > 23:
        st.subheader("💡 Рекомендация ИИ")
        st.info(
            "Зафиксирована аномалия VTEC. Проверьте корреляцию с геомагнитным Kp-индексом (сейчас он {:.1f}).".format(
                df['Kp'].mean()))

except FileNotFoundError:
    st.warning("Данные не найдены. Нажмите кнопку обновления.")
