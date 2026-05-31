import streamlit as st
import georinex as gr
import requests
import earthaccess
import gzip
import shutil
import os

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ IONEX")

# Инициализация сессии (earthaccess автоматически ищет логин/пароль в Secrets)
try:
    auth = earthaccess.login(persist=True)
    session = auth.get_session()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}")
    st.info("Убедитесь, что в Secrets добавлены EARTHDATA_USERNAME и EARTHDATA_PASSWORD")

url = "https://cddis.nasa.gov/archive/gnss/products/ionex/2026/150/casg1500.26i.Z"

if st.button("🚀 Загрузить и обработать IONEX"):
    with st.spinner("Авторизованное скачивание и распаковка..."):
        try:
            local_filename = "casg1500.26i.Z"

            # Скачивание через авторизованную сессию
            response = session.get(url, stream=True)
            if response.status_code == 200:
                with open(local_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                final_path = "data.ionex"

                # Распаковка
                with gzip.open(local_filename, 'rb') as f_in:
                    with open(final_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # Чтение через georinex
                ds = gr.load(final_path)

                st.success("Данные успешно считаны!")
                fig, ax = plt.subplots(figsize=(10, 6))

                if 'TEC' in ds:
                    ds['TEC'].isel(time=0).plot(ax=ax)
                    st.pyplot(fig)
                else:
                    st.write("Структура данных:", ds)
            else:
                st.error(f"Ошибка доступа: сервер вернул код {response.status_code}. Проверьте Secrets.")

        except Exception as e:
            st.error(f"Ошибка обработки: {e}")