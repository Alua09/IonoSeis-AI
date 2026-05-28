import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime

# 1. Настройка страницы
st.set_page_config(page_title="IonoSeis AI", layout="wide")

def get_live_data():
    stations = ["ALMA", "ASTN", "SHYM", "TALD"]
    data = []
    for s in stations:
        vtec = np.random.uniform(10, 28)
        kp = np.random.uniform(0, 7)
        data.append({"Station": s, "VTEC": vtec, "Kp": kp})
    return pd.DataFrame(data)

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

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Мониторинг станций (VTEC)")
    fig = px.bar(df, x='Station', y='VTEC', color='VTEC', 
                 color_continuous_scale='RdYlGn_r', title="Уровень ионизации (VTEC)")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🤖 Вердикт ИИ-анализатора")
    vtec_mean = df['VTEC'].mean()
    kp_mean = df['Kp'].mean()
    
    # --- НОЧНОЙ ФИЛЬТР ---
    current_hour = datetime.datetime.now().hour
    is_night = current_hour >= 22 or current_hour <= 6
    threshold = 18 if is_night else 23
    
    st.write(f"Текущее время: **{datetime.datetime.now().strftime('%H:%M')}**")
    st.write(f"Порог аномалий: **{threshold} TECU** {'(ночной режим)' if is_night else ''}")
    st.write(f"Средний VTEC: **{vtec_mean:.1f}** TECU")
    st.write(f"Глобальный Kp-индекс: **{kp_mean:.1f}**")
    st.markdown("---")
    
    if vtec_mean > threshold:
        if kp_mean < 3:
            st.error("🚨 ВНИМАНИЕ: Аномалия VTEC при низком Kp! Высокая вероятность сейсмической подготовки.")
        else:
            st.warning("⚠️ Возмущение ионосферы, вероятно, вызвано геомагнитной бурей.")
    else:
        if kp_mean > 5:
            st.warning("ℹ️ Высокая солнечная активность, ионосфера нестабильна.")
        else:
            st.success("✅ Состояние ионосферы стабильно (норма).")

st.markdown("---")
st.expander("Техническая справка").write("Алгоритм использует динамический порог чувствительности (18/23 TECU) для адаптации к суточному ходу ионизации.")
