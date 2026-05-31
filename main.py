import streamlit as st
import requests

st.title("🛰 IonoSeis: Мониторинг")
ALMATY_LAT, ALMATY_LON = 43.25, 76.92

if st.button("🚀 ОБНОВИТЬ ДАННЫЕ"):
    # 1. Сейсмика
    try:
        r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=20", timeout=10)
        if r.status_code == 200:
            data = r.json()
            st.subheader("Сейсмика (Алматы 1000 км)")
            found = False
            for f in data['features']:
                lon, lat = f['geometry']['coordinates'][:2]
                dist = ((lat - ALMATY_LAT)**2 + (lon - ALMATY_LON)**2)**0.5 * 111
                if dist < 1000:
                    st.write(f"🔹 {f['properties']['place']} | M: {f['properties']['mag']}")
                    found = True
            if not found: st.info("Спокойно.")
    except Exception as e:
        st.error(f"Сейсмика недоступна: {e}")

    # 2. Kp-индекс (облегченный запрос)
    try:
        # Используем альтернативный "прямой" сервис NOAA
        k = requests.get("https://services.swpc.noaa.gov/products/noaa-k-index.json", timeout=10).json()
        kp_val = k[-1][1]
        st.metric("Kp-индекс (геомагнитный фон)", kp_val)
    except:
        st.warning("Kp-индекс временно недоступен.")