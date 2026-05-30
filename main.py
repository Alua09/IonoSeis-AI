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

# Инициализация авторизации
try:
    earthaccess.login()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}")

if st.button("🚀 Анализировать актуальные данные"):
    with st.spinner("Загрузка и обработка..."):
        try:
            # 1. Поиск данных
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
                count=1
            )

            if not results:
                st.error("Данные за последний месяц не найдены.")
            else:
                # 2. Скачивание
                files = earthaccess.download(results, "data")
                raw_path = str(files[0])

                # 3. Распаковка (для надежности)
                path = raw_path
                if raw_path.endswith('.Z') or raw_path.endswith('.gz'):
                    path = raw_path.replace('.Z', '').replace('.gz', '') + ".rnx"
                    with gzip.open(raw_path, 'rb') as f_in:
                        with open(path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)

                # 4. Чтение БЕЗ параметра file_type
                ds = gr.load(path)

                # 5. Визуализация
                st.success("Данные успешно получены!")
                fig, ax = plt.subplots(figsize=(10, 6))

                # Если в данных есть TEC, строим его
                if 'TEC' in ds:
                    ds['TEC'].plot(ax=ax)
                else:
                    # Если данные имеют другую структуру, выводим что внутри
                    st.write("Найдена структура:", ds)

                st.pyplot(fig)

        except Exception as e:
            st.error(f"Ошибка при обработке: {e}")