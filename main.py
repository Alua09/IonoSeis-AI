import streamlit as st
import earthaccess
import georinex as gr
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import subprocess
import os

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ данных IONEX")

try:
    earthaccess.login()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}")

if st.button("🚀 Анализировать актуальные данные"):
    with st.spinner("Загрузка и обработка данных..."):
        try:
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
                files = earthaccess.download(results, "data")
                raw_path = str(files[0])

                # Используем системную утилиту 'gunzip', которая лучше понимает .Z файлы
                if raw_path.endswith('.Z'):
                    # Переименовываем файл, чтобы у него было расширение .Z для gunzip
                    uncompressed_path = raw_path.replace('.Z', '.rnx')
                    # Вызываем системную команду для распаковки
                    subprocess.run(['gunzip', '-c', raw_path], stdout=open(uncompressed_path, 'wb'), check=True)
                    path = uncompressed_path
                else:
                    path = raw_path

                # Чтение
                ds = gr.load(path)

                st.success("Данные успешно получены!")
                fig, ax = plt.subplots(figsize=(10, 6))

                if 'TEC' in ds:
                    ds['TEC'].plot(ax=ax)
                    st.pyplot(fig)
                else:
                    st.write("Структура данных:", ds)

        except Exception as e:
            st.error(f"Ошибка при обработке: {e}. Возможно, формат файла не поддерживается.")