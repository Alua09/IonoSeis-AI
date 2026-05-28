import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Настройка страницы
st.set_page_config(page_title="IonoSeis AI", layout="wide")

# Функция генерации данных (имитация API IGS)
def get_live_data():
    stations = ["ALMA", "ASTN", "SHYM", "TALD"]
    data = []
    for s in stations:
        # VTEC: ионосферная плотность, Kp: геомагнитная активность
        vtec = np.random.uniform(10, 28)
        kp = np.random.uniform(0, 7)
        data.append({"Station": s, "VTEC": vtec, "Kp": kp})
    return pd.DataFrame(data)

# Интерфейс
st.title("🛰 IonoSeis: Интеллектуальный сейсмо-ионосферный мониторинг")
st.markdown("---")

if st.button("🔄 Обновить данные с серверов"):
    df = get_live_data()
    df.to_csv("live_data.csv", index=False)
    st.rerun()

try:
    df = pd.read_csv("live_data.csv")
except:
    df = get_live_data()

# Анализ данных и светофор
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Мониторинг станций")
    fig = px.bar(df, x='Station', y='VTEC', color='VTEC', 
                 color_continuous_scale='RdYlGn_r', title="Уровень ионизации (VTEC)")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Вердикт ИИ")
    vtec_mean = df['VTEC'].mean()
    kp_mean = df['Kp'].mean()
    
    # Логика анализа
    if vtec_mean > 23 and kp_mean < 3:
        st.error(f"🚨 ВЫСОКИЙ РИСК: Аномалия VTEC ({vtec_mean:.1f}) при спокойном фоне ({kp_mean:.1f}).")
    elif vtec_mean > 23 and kp_mean >= 3:
        st.warning(f"⚠️ ПОВЫШЕННЫЙ ФОН: Вероятно влияние солнечной активности (Kp: {kp_mean:.1f}).")
    else:
        st.success(f"✅ Сейсмический фон в норме (VTEC: {vtec_mean:.1f}).")

st.markdown("---")
st.write("### Технические показатели станций")
st.dataframe(df)
