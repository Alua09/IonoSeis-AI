import streamlit as st
import requests

st.title("🛰 IonoSeis: Мониторинг Алматы")
ALMATY_LAT, ALMATY_LON = 43.25, 76.92

if st.button("🔄 ОБНОВИТЬ ДАННЫЕ"):
    # Сейсмика: остается самым стабильным каналом
    st.subheader("Сейсмическая активность (USGS)")
    try:
        r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=20", timeout=10)
        data = r.json()
        found = False
        for f in data['features']:
            lon, lat = f['geometry']['coordinates'][:2]
            dist = ((lat - ALMATY_LAT) ** 2 + (lon - ALMATY_LON) ** 2) ** 0.5 * 111
            if dist < 1000 and f['properties']['mag'] > 2.0:
                st.write(
                    f"🔹 {f['properties']['place']} | Магнитуда: {f['properties']['mag']} | Расстояние: {round(dist)} км")
                found = True
        if not found:
            st.info("Сейсмически спокойно в радиусе 1000 км.")
    except:
        st.warning("Сервер сейсмики недоступен.")

    # Геомагнитный фон: теперь через визуальный индикатор (без API)
    st.subheader("Геомагнитная обстановка")
    st.markdown("Следите за текущим статусом Kp-индекса на официальном портале:")
    st.link_button("Открыть SpaceWeatherLive (Kp-индекс)",
                   "https://www.spaceweatherlive.com/en/solar-activity/kp-index.html")

    st.info(
        "💡 Совет: Если вы видите, что Kp-индекс выше 5 (красная зона), значит, ионосфера возмущена солнечной активностью.")

st.sidebar.markdown("""
### Ваша система готова.
Сейчас приложение работает как «окно» в данные. 
Если вы хотите собирать статистику (лог), напишите мне, и мы добавим функцию сохранения всех землетрясений в текстовый файл прямо на вашем компьютере.
""")