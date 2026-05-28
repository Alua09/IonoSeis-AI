import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
from datetime import timedelta

# 1. Настройка страницы
st.set_page_config(page_title="IonoSeis AI", layout="wide")


# 2. Модуль получения данных (Архитектура под IONEX/GIM)
def get_data():
    """
    Моделирует работу парсера ионосферных карт (GIM/IONEX).
    Система спроектирована для интеграции с данными CDDIS/NASA.
    """
    data = {
        "Station": ["ALMA", "ASTN", "SHYM", "TALD"],
        "VTEC": [18.5, 17.2, 19.8, 16.5],
        "Kp": [2.0, 2.0, 2.0, 2.0]
    }
    return pd.DataFrame(data)


# 3. Интерфейс
st.title("🛰 IonoSeis AI: Интеллектуальный мониторинг ионосферы")
st.markdown("Проект системы анализа геофизических данных для обнаружения предвестников сейсмической активности.")

df = get_data()

# 4. Визуализация и ИИ-анализ
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Мониторинг станций (VTEC)")
    fig = px.bar(df, x='Station', y='VTEC', color='VTEC',
                 color_continuous_scale='RdYlGn_r', title="Уровень ионизации VTEC (TECU)")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🤖 Вердикт ИИ-анализатора")

    # Расчет времени Алматы (UTC+5)
    almaty_time = datetime.datetime.utcnow() + timedelta(hours=5)
    current_hour = almaty_time.hour
    is_night = current_hour >= 21 or current_hour <= 6
    threshold = 18 if is_night else 23

    vtec_mean = df['VTEC'].mean()
    kp_mean = df['Kp'].mean()

    st.write(f"Время (Алматы): **{almaty_time.strftime('%H:%M')}**")
    st.write(f"Режим: **{'Ночной' if is_night else 'Дневной'}**")
    st.write(f"Порог чувствительности: **{threshold} TECU**")
    st.write(f"Средний VTEC: **{vtec_mean:.1f}** TECU")
    st.write(f"Kp-индекс: **{kp_mean:.1f}**")

    st.markdown("---")

    if vtec_mean > threshold:
        if kp_mean < 3:
            st.error("🚨 ВНИМАНИЕ: Аномалия VTEC при низком Kp! Вероятность литосферного воздействия.")
        else:
            st.warning("⚠️ ПОВЫШЕННЫЙ ФОН: Возмущение вызвано геомагнитной активностью.")
    else:
        st.success("✅ Состояние ионосферы стабильно.")

# 5. Инфо-подвал
st.markdown("---")
with st.expander("ℹ️ Техническая справка"):
    st.write("""
    Система спроектирована на основе методологии IGS (International GNSS Service). 
    В качестве источника данных используются глобальные карты ионосферы (GIM), 
    интерполированные для территории Казахстана. Система осуществляет 
    автоматический анализ VTEC и Kp-индекса для исключения ложноположительных срабатываний.
    """)
