import streamlit as st
import requests

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis Pro: Аналитика")
st.title("🛰 IonoSeis Pro: Мониторинг безопасности Алматы")

# Координаты Алматы
ALMATY_LAT, ALMATY_LON = 43.25, 76.92

if st.button("🚀 ПРОВЕРИТЬ СЕЙСМИЧЕСКУЮ ОБСТАНОВКУ"):
    # 1. Сейсмика (Стабильный модуль USGS)
    try:
        r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=50", timeout=15)
        if r.status_code == 200:
            data = r.json()
            st.subheader("Сейсмика в радиусе 1000 км")

            danger_detected = False
            for f in data['features']:
                lon, lat = f['geometry']['coordinates'][:2]
                dist = ((lat - ALMATY_LAT) ** 2 + (lon - ALMATY_LON) ** 2) ** 0.5 * 111
                mag = f['properties']['mag']

                # Фильтр: только интересные события
                if dist < 1000 and mag > 2.0:
                    text = f"🔹 {f['properties']['place']} | Магнитуда: {mag} | Расстояние: {round(dist)} км"
                    if mag >= 4.0 or dist < 300:
                        st.error(f"⚠️ ТРЕВОГА: {text}")
                        danger_detected = True
                    else:
                        st.write(text)

            if not danger_detected:
                st.info("В радиусе 1000 км значимых сейсмических событий нет.")
        else:
            st.error("Сервер USGS временно недоступен.")
    except Exception as e:
        st.error(f"Ошибка соединения: {e}")

    # 2. Kp-индекс (Геомагнитный фон)
    st.subheader("Геомагнитная активность")
    try:
        # Используем альтернативный API для Kp, который лояльнее к запросам
        resp = requests.get("https://services.swpc.noaa.gov/products/noaa-k-index.json", timeout=10)
        if resp.status_code == 200:
            kp_val = resp.json()[-1][1]
            st.metric("Глобальный Kp-индекс", kp_val)
        else:
            st.warning("Геомагнитные данные сейчас недоступны (ограничение сервера).")
    except:
        st.warning("Сервер геомагнитных данных не ответил.")

st.sidebar.markdown("""
### Рекомендации:
* **Зеленый статус**: Спокойно.
* **⚠️ ТРЕВОГА**: События > 4.0 или ближе 300 км.
* Если API NOAA (Kp) недоступен — это ограничение облачного сервера, попробуйте запустить этот же код локально на компьютере для 100% стабильности.
""")