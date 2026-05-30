import streamlit as st
import earthaccess
import georinex as gr
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import subprocess

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ данных")

try:
    earthaccess.login()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}")

if st.button("🚀 Анализировать актуальные данные"):
    with st.spinner("Загрузка и обработка..."):
        try:
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
                files = earthaccess.download(results, "data")
                raw_path = str(files[0])

                # Если файл сжат (.Z или .gz), попробуем его распаковать
                # Используем более универсальный подход для файлов NASA
                path = raw_path
                if raw_path.endswith('.Z') or raw_path.endswith('.gz'):
                    unpacked_path = raw_path.replace('.Z', '').replace('.gz', '') + ".rnx"
                    # Используем системный gunzip, если он доступен в контейнере,
                    # либо просто переименовываем, если это стандартный RINEX
                    import gzip

                    with gzip.open(raw_path, 'rb') as f_in:
                        with open(unpacked_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    path = unpacked_path

                # Чтение с явным указанием, что это IONEX
                ds = gr.load(path, file_type='ionex')

                st.success("Данные успешно получены!")
                fig, ax = plt.subplots(figsize=(10, 6))

                if 'TEC' in ds:
                    ds['TEC'].plot(ax=ax)
                    st.pyplot(fig)
                else:
                    st.write("Структура данных:", ds)

        except Exception as e:
            st.error(f"Ошибка при обработке: {e}")