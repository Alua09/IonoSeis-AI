import streamlit as st
import earthaccess
import georinex as gr
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import gzip
import shutil
import os

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ данных IONEX")

try:
    earthaccess.login()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}")

if st.button("🚀 Анализировать актуальные данные"):
    with st.spinner("Распаковка и чтение данных..."):
        try:
            # 1. Поиск
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
                count=1
            )

            if not results:
                st.error("Данные не найдены.")
            else:
                # 2. Скачивание
                files = earthaccess.download(results, "data")
                raw_path = str(files[0])
                unpacked_path = raw_path + ".uncompressed"

                # 3. Гарантированная распаковка GZIP
                with gzip.open(raw_path, 'rb') as f_in:
                    with open(unpacked_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # 4. Чтение
                ds = gr.load(unpacked_path)

                # 5. Визуализация
                st.success("Данные успешно считаны!")
                fig, ax = plt.subplots(figsize=(10, 6))

                # В данных IONEX VTEC часто находится в переменной 'TEC'
                if 'TEC' in ds:
                    ds['TEC'].isel(time=0).plot(ax=ax)  # Берем первый временной шаг
                    st.pyplot(fig)
                else:
                    st.write("Структура данных:", ds)

        except Exception as e:
            st.error(f"Ошибка при обработке: {e}")