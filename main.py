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

if st.button("🚀 Найти и загрузить актуальный IONEX"):
    with st.spinner("Поиск актуальных данных..."):
        try:
            # 1. Поиск актуального файла через метаданные NASA
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=('2026-05-25', '2026-05-31'),
                count=1
            )

            if not results:
                st.error("Файлы не найдены в архиве.")
            else:
                # Получаем прямую URL-ссылку из найденного результата
                data_url = results[0].data_links()[0]
                st.write(f"Найден файл: {data_url}")

                # 2. Скачивание найденного файла через сессию
                response = session.get(data_url, stream=True)

                if response.status_code == 200:
                    local_filename = "data.ionex.Z"
                    with open(local_filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    # ... далее код распаковки и gr.load(final_path) ...
                    st.success("Данные успешно скачаны!")
                else:
                    st.error(f"Ошибка при скачивании {data_url}: код {response.status_code}")

        except Exception as e:
            st.error(f"Ошибка: {e}")