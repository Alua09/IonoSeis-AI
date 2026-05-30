import streamlit as st
import earthaccess
import georinex as gr
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ данных IONEX")

# Инициализация авторизации
try:
    earthaccess.login()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}. Проверьте Secrets в настройках приложения.")

if st.button("🚀 Анализировать актуальные данные"):
    with st.spinner("Поиск и загрузка данных..."):
        try:
            # 1. Поиск данных за последние 30 дней, чтобы избежать 404 ошибок
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
                count=1
            )

            if not results:
                st.error("Данные за последний месяц не найдены. Попробуйте расширить диапазон поиска.")
            else:
                # 2. Скачивание
                files = earthaccess.download(results, "data")
                path = files[0]

                # 3. Чтение через georinex
                ds = gr.load(path)

                # 4. Визуализация
                st.success("Данные успешно загружены!")
                fig, ax = plt.subplots(figsize=(10, 6))

                # В IONEX файлах данные обычно в переменной 'TEC'
                if 'TEC' in ds:
                    ds['TEC'].plot(ax=ax)
                    st.pyplot(fig)
                else:
                    st.write("Структура данных:", ds)

        except Exception as e:
            st.error(f"Ошибка при обработке: {e}")