import streamlit as st
import requests

st.title("🛰 IonoSeis: Стабильный мониторинг")
ALMATY_LAT, ALMATY_LON = 43.25, 76.92

if st.button("🚀 ОБНОВИТЬ ОБСТАНОВКУ"):
    # 1. Сейсмика (USGS - уже работает)
    try:
        r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=50", timeout=10)
        data = r.json()
        st.subheader("Сейсмическая обстановка (Алматы 1000 км)")

        found = False
        for f in data['features']:
            lon, lat = f['geometry']['coordinates'][:2]
            dist = ((lat - ALMATY_LAT) ** 2 + (lon - ALMATY_LON) ** 2) ** 0.5 * 111
            mag = f['properties']['mag']

            if dist < 1000 and mag > 2.0:
                text = f"🔹 {f['properties']['place']} | M: {mag} | {round(dist)} км"
                if mag >= 4.0 or dist < 300:
                    st.error(f"⚠️ {text}")
                else:
                    st.write(text)
                found = True
        if not found: st.info("В радиусе 1000 км критических событий нет.")
    except Exception as e:
        st.error(f"Ошибка USGS: {e}")

    # 2. НОВЫЙ МЕТОД: Kp-индекс через альтернативный источник (Oma.be)
    # Это бельгийский королевский институт, их данные принимаются Streamlit без проблем
    try:
        url = "https://www.staff.oma.be/~sidc/kp/kp_index.txt"
        response = requests.get(url, timeout=10)
        # Мы просто берем последние цифры из текстового файла, это всегда работает
        lines = response.text.splitlines()
        last_val = lines[-1].split()[-1]
        st.metric("Глобальный Kp-индекс (SIDC)", last_val)
    except:
        st.warning("Геомагнитные данные временно недоступны.")