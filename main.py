import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime
from datetime import timedelta

# 1. Настройка страницы
st.set_page_config(page_title="IonoSeis AI", layout="wide")

# 2. Функция генерации данных
def get_live_data():
    stations = ["ALMA", "ASTN", "SHYM", "TALD"]
    data = []
    for s in stations:
        # VTEC: 10-28, Kp: 0-7
        vtec = np.random.uniform(10, 28)
        kp = np.random.uniform(0, 7)
        data.append({"Station": s, "VTEC": vtec, "Kp": kp})
    return pd.DataFrame(data)

# 3. Интерфейс
st.title("🛰 IonoSeis: Интеллектуальный сейсмо-ионосферный мониторинг")
st.markdown("---")

if st.button("🔄 Обновить данные"):
    df = get_live_data()
    df.to_csv("live_data.csv", index=False)
    st.rerun()

try:
    df = pd.read_csv("live_data.csv")
except:
    df = get_live_data()

# 4. Аналитика и визуализация
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Мониторинг станций (VTEC)")
    fig = px.bar(df, x='Station', y='VTEC', color='VTEC', 
                 color_continuous_scale='RdYlGn_r', title="Уровень ионизации (VTEC)")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🤖 Вердикт ИИ-анализатора")
    
    # Работа со временем Алматы (UTC+5)
    almaty_time = datetime.datetime.utcnow() + timedelta(hours=5)
    current_hour = almaty_time.hour
    
    # Логика ночного режима
    is_night = current_hour >= 21 or current_hour <= 6
    threshold = 18 if is_night else 23
    
    vtec_mean = df['VTEC'].mean()
    kp_mean = df['Kp'].mean()
    
    st.write(f"Время (Алматы): **{almaty_time.strftime('%H:%M')}**")
    st.write(f"Порог чувствительности: **{threshold} TECU** {'(ночной)' if is_night else '(дневной)'}")
    st.write(f"Средний VTEC: **{vtec_mean:.1f}** TECU")
    st.write(f"Kp-индекс: **{kp_mean:.1f}**")
    st.markdown("---")
    
    # Аналитическая логика
    if vtec_mean > threshold:
        if kp_mean < 3:
            st.error("🚨 ВНИМАНИЕ: Аномалия VTEC при низком Kp! Высокая вероятность литосферного воздействия.")
        else:
            st.warning("⚠️ ПОВЫШЕННЫЙ ФОН: Вомущение ионосферы, вероятно, вызвано геомагнитной бурей.")
    else:
        if kp_mean > 5:
            st.warning("ℹ️ Высокая солнечная активность, ионосфера нестабильна.")
        else:
            st.success("✅ Состояние ионосферы стабильно. Предвестников не обнаружено.")

# 5. Технический подвал
st.markdown("---")
with st.expander("Как работает система?"):
    st.write("""
    Система анализирует плотность электронов (VTEC) и сопоставляет её с геомагнитной активностью (Kp-индекс).
    При превышении порога система автоматически определяет природу аномалии: 
    тектоническая (сейсмическая) или космическая (солнечная).
    """)
    st.dataframe(df)
