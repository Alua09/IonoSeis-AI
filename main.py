import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="IonoSeis AI Contest")
st.title("🛰 IonoSeis: Мониторинг для конкурса")


# Используем надежный Proxy, который GitHub Actions "пропускает" без блокировок
# Мы берем данные через сервис "allorigins", он превращает любой сложный API в простой текст
def get_safe_data(url):
    proxy_url = f"https://api.allorigins.win/get?url={requests.utils.quote(url)}"
    response = requests.get(proxy_url, timeout=10)
    return response.json()['contents']


if st.button("🚀 ОБНОВИТЬ ДАННЫЕ (GITHUB READY)"):
    try:
        # 1. Сейсмика через прокси
        seis_url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&limit=5&minmagnitude=3"
        csv_data = get_safe_data(seis_url)
        from io import StringIO

        df = pd.read_csv(StringIO(csv_data))

        st.subheader("Сейсмические события")
        st.write(df[['time', 'place', 'mag']])

        # 2. Kp-индекс через прокси
        kp_url = "https://kp.gfz-potsdam.de/app/files/Kp_ap_Ap_SN_F10.7_nowcast.txt"
        kp_text = get_safe_data(kp_url)
        last_val = [line for line in kp_text.splitlines() if not line.startswith('#')][-1].split()[2]

        st.metric("Kp-индекс (GFZ)", last_val)
        st.success("Данные успешно получены через GitHub Proxy!")

    except Exception as e:
        st.error(f"Ошибка загрузки: {e}")
        st.write("Если вы видите это в GitHub Actions, проверьте наличие библиотеки pandas в requirements.txt")