import streamlit as st
import earthaccess
import georinex as gr
import matplotlib.pyplot as plt
import os
import shutil

# Настройка страницы
st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ данных IONEX")

# Инициализация авторизации
# earthaccess сам ищет переменные окружения EARTHDATA_USERNAME и EARTHDATA_PASSWORD,
# которые мы прописали в "Secrets" на сайте Streamlit.
try:
    earthaccess.login()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}. Проверьте Secrets в настройках приложения.")

# Кнопка для запуска
if st.button("🚀 Анализировать данные IGS"):
    with st.spinner("Поиск и загрузка данных..."):
        try:
            # 1. Поиск данных (используем проверенный short_name)
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                count=1
            )

            if not results:
                st.error("Данные не найдены.")
            else:
                # 2. Скачивание
                files = earthaccess.download(results, "data")
                path = files[0]

                # 3. Чтение через georinex
                ds = gr.load(path)

                # 4. Визуализация
                st.success("Данные успешно загружены!")
                fig, ax = plt.subplots(figsize=(10, 6))

                if 'TEC' in ds:
                    ds['TEC'].plot(ax=ax)
                    st.pyplot(fig)
                else:
                    st.write("Структура данных:", ds)

        except Exception as e:
            st.error(f"Ошибка при обработке файла: {e}")