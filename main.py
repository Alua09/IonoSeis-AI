import streamlit as st
import requests
import earthaccess
import gzip
import shutil
import xarray as xr
import os

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ IONEX")

# 1. Авторизация
try:
    auth = earthaccess.login(persist=True)
    session = auth.get_session()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}")
    st.stop()

if st.button("🚀 Начать анализ"):
    with st.spinner("Загрузка и диагностика..."):
        try:
            # 2. Поиск файла
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=('2026-05-20', '2026-05-31'),
                count=1
            )

            if not results:
                st.error("Данные не найдены.")
            else:
                data_url = results[0].data_links()[0]
                st.write(f"Файл: {data_url}")

                # 3. Скачивание
                response = session.get(data_url, stream=True)
                local_filename = "data.inx.gz"
                with open(local_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # 4. Распаковка
                final_path = "data.ionex"
                with gzip.open(local_filename, 'rb') as f_in:
                    with open(final_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # 5. Диагностика (выводим начало файла, чтобы понять формат)
                with open(final_path, 'r', encoding='ascii', errors='ignore') as f:
                    lines = [f.readline() for _ in range(15)]

                st.write("### 📄 Первые 15 строк файла (Диагностика):")
                st.code("".join(lines))

                st.info(
                    "Скопируйте эти строки и пришлите мне — это поможет мне написать точный парсер для ваших данных.")

        except Exception as e:
            st.error(f"Ошибка: {e}")