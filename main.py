import streamlit as st
import pandas as pd
import requests

# Настройка страницы
st.set_page_config(page_title="IonoSeis Pro: Алматы", layout="wide")
st.title("🛰 IonoSeis: Сейсмический монитор Алматы")

# Координаты Алматы
ALMATY_LAT, ALMATY_LON = 43.25, 76.92


# Функция получения сейсмики (самый стабильный API USGS)
@st.cache_data(ttl=600)
def get_seismic_data():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=200&minmagnitude=2"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        return None
    return None


# Интерфейс
if st.button("🚀 ЗАГРУЗИТЬ / ОБНОВИТЬ ДАННЫЕ"):
    data = get_seismic_data()

    if data:
        features = data.get('features', [])
        if features:
            records = []
            for f in features:
                props = f.get('properties', {})
                coords = f.get('geometry', {}).get('coordinates', [0, 0])
                records.append({
                    'place': props.get('place', 'N/A'),
                    'mag': props.get('mag', 0),
                    'lat': coords[1],
                    'lon': coords[0]
                })

            df = pd.DataFrame(records)
            # Фильтр: расстояние до Алматы < 300 км
            df['dist'] = ((df['lat'] - ALMATY_LAT) ** 2 + (df['lon'] - ALMATY_LON) ** 2) ** 0.5 * 111
            local = df[df['dist'] < 300].sort_values(by='dist')

            st.subheader("⚠️ Сейсмические события (Радиус 300 км от Алматы)")
            if not local.empty:
                st.dataframe(local[['place', 'mag', 'dist']], use_container_width=True)
            else:
                st.info("В радиусе 300 км событий не зафиксировано.")
        else:
            st.warning("Данные USGS вернули пустой список.")
    else:
        st.error("Ошибка сети: не удалось подключиться к серверу USGS.")

# Дополнительная информация для пользователя
st.sidebar.markdown("---")
st.sidebar.write("### Статус: Активен")
st.sidebar.write("Мониторинг настроен на регион Алматы (300 км).")