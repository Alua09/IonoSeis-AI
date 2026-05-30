import streamlit as st
import earthaccess
import georinex as gr
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import gzip
import shutil
import os

# Настройка страницы
st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ данных IONEX")

# Инициализация авторизации
# Библиотека автоматически ищет EARTHDATA_USERNAME и EARTHDATA_PASSWORD в Secrets
try:
    earthaccess.login()
except Exception as e:
    st.error(
        f"Ошибка авторизации: {e}. Убедитесь, что логин и пароль добавлены в Settings -> Secrets на сайте Streamlit.")

if st.button("🚀 Анализировать актуальные данные"):
    with st.spinner("Поиск и обработка данных..."):
        try:
            # 1. Поиск данных за последние 30 дней
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
                raw_path = files[0]

                # 3. Принудительная распаковка (если нужно)
                path = raw_path
                if raw_path.endswith('.Z') or raw_path.endswith('.gz'):
                    path = raw_path.replace('.Z', '').replace('.gz', '') + ".unpacked"
                    with gzip.open(raw_path, 'rb') as f_in:
                        with open(path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)

                # 4. Чтение через georinex
                ds = gr.load(path)

                # 5. Визуализация
                st.success("Данные успешно получены!")
                fig, ax = plt.subplots(figsize=(10, 6))

                if 'TEC' in ds:
                    ds['TEC'].plot(ax=ax)
                    st.pyplot(fig)
                else:
                    st.write("Структура данных:", ds)

        except Exception as e:
            st.error(f"Ошибка при обработке: {e}")