import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Настройка страницы
st.set_page_config(page_title="IonoSeis AI", layout="wide")

# 2. Функция генерации данных (имитация API научных станций)
def get_live_data():
    stations = ["ALMA", "ASTN", "SHYM", "TALD"]
    data = []
    for s in stations:
        # VTEC: электронная плотность (основной индикатор)
        # Kp: геомагнитный индекс (фильтр космической погоды)
        vtec = np.random.uniform(10, 28)
        kp = np.random.uniform(0, 7)
        data.append({"Station": s, "VTEC": vtec, "Kp": kp})
    return pd.DataFrame(data)

# 3. Заголовок и управление
st.title("🛰 IonoSeis: Интеллектуальный сейсмо-ионосферный мониторинг")
st.markdown("---")

if st.button("🔄 Обновить данные в реальном времени"):
    df = get_live_data()
    df.to_csv("live_data.csv", index=False)
    st.rerun()

# 4. Загрузка данных
try:
    df = pd.read_csv("live_data.csv")
except:
    df = get_live_data()

# 5. Визуализация и Аналитика
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Мониторинг станций (VTEC)")
    fig = px.bar(df, x='Station', y='VTEC', color='VTEC', 
                 color_continuous_scale='RdYlGn_r', title="Уровень ионизации (VTEC) по станциям")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🤖 Вердикт ИИ-анализатора")
    vtec_mean = df['VTEC'].mean()
    kp_mean = df['Kp'].mean()
    
    st.write(f"Средний VTEC: **{vtec_mean:.1f}** TECU")
    st.write(f"Глобальный Kp-индекс: **{kp_mean:.1f}**")
    st.markdown("---")
    
    # Интеллектуальная логика фильтрации "шумов"
    if vtec_mean > 23:
        if kp_mean < 3:
            st.error("🚨 ВНИМАНИЕ: Аномалия VTEC при низком Kp-индексе! Высокая вероятность литосферного воздействия (предвестник).")
        else:
            st.warning("⚠️ ПОВЫШЕННЫЙ ФОН: Вомущение ионосферы, вероятно, вызвано геомагнитной бурей (высокий Kp).")
    else:
        if kp_mean > 5:
            st.warning("ℹ️ Высокая солнечная активность, ионосфера нестабильна.")
        else:
            st.success("✅ Состояние ионосферы стабильно. Сейсмических предвестников не обнаружено.")

# 6. Дополнительная техническая информация
st.markdown("---")
with st.expander("Технические подробности"):
    st.write("Система анализирует вертикальное полное электронное содержание (VTEC) в ионосфере. При подготовке землетрясений фиксируются аномалии плотности электронов, которые система фильтрует по глобальному Kp-индексу для исключения влияния солнечной погоды.")
    st.dataframe(df)
