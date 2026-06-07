import streamlit as st
import requests
from datetime import datetime, timedelta

# Настройка страницы
st.set_page_config(layout="wide", page_title="IonoSeis AI")

st.title("🛰 IonoSeis AI: Аналитическая панель")

# Вкладки
tab1, tab2 = st.tabs(["🟢 Мониторинг (Live)", "📂 Архив землетрясений"])

with tab1:
    st.write("### Система мониторинга активна")
    st.info("Система работает в штатном режиме.")

with tab2:
    st.write("### Архив сейсмических данных (USGS)")

    # Выбор параметров
    city = st.selectbox("Выберите город:", ["Алматы", "Бишкек", "Токио"])
    date_start = st.date_input("Дата начала:", datetime.now() - timedelta(days=30))

    if st.button("Загрузить данные из архива"):
        coords = {
            "Алматы": (43.25, 76.92),
            "Бишкек": (42.87, 74.59),
            "Токио": (35.68, 139.65)
        }
        lat, lon = coords[city]

        # Формируем URL
        # minmagnitude=2.0 - ищем только ощутимые события
        url = (f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
               f"&starttime={date_start.isoformat()}"
               f"&endtime={(date_start + timedelta(days=30)).isoformat()}"
               f"&latitude={lat}&longitude={lon}&maxradiuskm=1000&minmagnitude=2.0")

        try:
            st.write(f"Запрос к серверу: [Нажмите, чтобы проверить ссылку]({url})")

            response = requests.get(url, timeout=10)
            data = response.json()
            features = data.get('features', [])

            st.write(f"Найдено событий: **{len(features)}**")

            if len(features) > 0:
                for f in features:
                    props = f['properties']
                    dt = datetime.fromtimestamp(props['time'] / 1000).strftime('%Y-%m-%d %H:%M')
                    st.write(f"📅 {dt} | 📍 {props['place']} | ⚡ Магнитуда: **{props['mag']}**")
            else:
                st.warning("За выбранный период событий не найдено. Попробуйте изменить даты.")

        except Exception as e:
            st.error(f"Произошла ошибка при загрузке: {e}")
            st.write("Возможно, ваш провайдер или Firewall блокирует доступ к сайту USGS.")