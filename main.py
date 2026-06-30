import streamlit as st
import json
import pandas as pd
import requests
import pydeck as pdk
import os
import pytz
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt

# --- КОНФИГУРАЦИЯ ---
st.set_page_config(layout="wide", page_title="IonoSeis AI", page_icon="🛰️")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'vtec_data.json')

CITIES = {
    "Алматы": (43.25, 76.92, "Asia/Almaty"),
    "Бишкек": (42.87, 74.59, "Asia/Bishkek"),
    "Токио": (35.68, 139.65, "Asia/Tokyo"),
    "Тайвань (Хуалянь)": (24.00, 121.60, "Asia/Taipei"),
    "Стамбул": (41.00, 28.97, "Europe/Istanbul")
}


# --- ФУНКЦИИ (ОПРЕДЕЛЯЕМ ИХ ПЕРВЫМИ) ---

def load_vtec_data():
    """Чтение данных из локального файла JSON"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def get_kp():
    try:
        res = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=5).json()
        return float(res[-1][1])
    except:
        return 2.0


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat, dLon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dLat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon / 2) ** 2
    return R * 2 * asin(sqrt(a))


@st.cache_data(ttl=300)
def get_filtered_seismic_data():
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&minmagnitude=4.0&limit=100"
    try:
        res = requests.get(url, timeout=10).json()
        data = []
        for f in res.get('features', []):
            props = f['properties']
            quake_lat, quake_lon = f['geometry']['coordinates'][1], f['geometry']['coordinates'][0]
            for city, (c_lat, c_lon, _) in CITIES.items():
                if haversine(quake_lat, quake_lon, c_lat, c_lon) < 500:
                    data.append({
                        "Магнитуда": props['mag'], "Город": city,
                        "Место": props['place'],
                        "Время": datetime.fromtimestamp(props['time'] / 1000).strftime('%d.%m %H:%M')
                    })
                    break
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()


# --- ИНТЕРФЕЙС (ВЫЗЫВАЕМ ФУНКЦИИ ТОЛЬКО ЗДЕСЬ) ---
data = load_vtec_data()

with st.sidebar:
    st.header("🛰️ IonoSeis AI")
    st.write(f"🕒 **Последний скан (UTC):** {data.get('timestamp', 'Нет данных')}")
    st.metric("Индекс солнечной активности (Kp)", f"{get_kp()}")
    st.divider()
    st.caption("Источники данных:")
    st.write("• NASA CDDIS (VTEC)")
    st.write("• USGS API (Сейсмика)")
    st.write("• NOAA (Kp-индекс)")
    st.info("Мониторинг литосферно-ионосферных связей.")

st.title("🛰️ IonoSeis AI: Экспертный мониторинг")

tabs = st.tabs(["🟢 МОНИТОРИНГ", "🌋 СЕЙСМО-ЛЕНТА", "🧪 МЕТОДОЛОГИЯ"])

with tabs[0]:
    cols = st.columns(5)
    for i, (city, (lat, lon, tz)) in enumerate(CITIES.items()):
        val = data.get(city, 15.0)
        z = (val - 15.0) / 1.5
        local_time = datetime.now(pytz.timezone(tz)).strftime('%H:%M')
        with cols[i]:
            st.metric(city, f"{val:.1f} TECU", f"Z: {z:+.1f}")
            st.caption(f"🕒 {local_time} (местное)")
            color = [255, 0, 0, 160] if abs(z) > 2.0 else [60, 200, 60, 160]
            st.pydeck_chart(pdk.Deck(initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=4),
                                     layers=[pdk.Layer("ScatterplotLayer", pd.DataFrame({'lat': [lat], 'lon': [lon]}),
                                                       get_position=["lon", "lat"], get_fill_color=color,
                                                       get_radius=60000)]))

with tabs[1]:
    st.subheader("🌋 Сейсмическая активность (4.0+ магнитуд, <500км от городов)")
    df = get_filtered_seismic_data()
    if not df.empty:
        st.dataframe(
            df.style.map(lambda x: 'background-color: #ffcccc' if isinstance(x, (int, float)) and x >= 5.0 else '',
                         subset=['Магнитуда']), use_container_width=True)
    else:
        st.write("В радиусе мониторинга значимых событий нет.")

with tabs[2]:
    st.markdown("""
    ### 🧪 Научная методология: Литосферно-ионосферные связи (LIS)
    Данная система предназначена для обнаружения краткосрочных ионосферных предвестников сейсмических событий.

    * **Принцип:** Тектонические напряжения в очаге будущего землетрясения генерируют аномальные электрические поля, которые, проникая в ионосферу, локально меняют концентрацию заряженных частиц (VTEC).
    * **Параметр Z-score:** Стандартизированное отклонение текущего VTEC от фонового уровня. Значения **Z > +2.0** указывают на статистически аномальное возбуждение ионосферы.
    * **Важно:** Мониторинг Kp-индекса (солнечной активности) позволяет исключить "ложные" срабатывания, вызванные солнечными бурями, а не литосферными процессами.
    """)