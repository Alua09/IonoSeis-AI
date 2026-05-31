import streamlit as st
import georinex as gr
import requests
import earthaccess
import gzip
import shutil
import matplotlib.pyplot as plt

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ IONEX")

# Инициализация авторизованной сессии
try:
    auth = earthaccess.login(persist=True)
    session = auth.get_session()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}")
    st.stop()

if st.button("🚀 Найти и проанализировать данные"):
    with st.spinner("Поиск и обработка..."):
        try:
            # Поиск файла через метаданные
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=('2026-05-20', '2026-05-31'),
                count=1
            )

            if not results:
                st.error("Данные не найдены.")
            else:
                data_url = results[0].data_links()[0]
                st.write(f"Загрузка файла: {data_url}")

                # Скачивание
                response = session.get(data_url, stream=True)
                local_filename = "data.inx.gz"
                with open(local_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # Распаковка
                final_path = "data.inx"
                with gzip.open(local_filename, 'rb') as f_in:
                    with open(final_path, 'wb') as f_in_file:
                        shutil.copyfileobj(f_in, f_in_file)

                # Чтение через georinex
                # Он возвращает xarray.Dataset, адаптированный для данных IONEX
                ds = gr.load(final_path)

                st.success("Данные успешно считаны через georinex!")
                st.write("Структура данных:", ds)

                fig, ax = plt.subplots(figsize=(10, 6))

                # Проверка ключей в датасете: обычно это 'TEC' или 'ionex'
                target_var = 'TEC' if 'TEC' in ds else list(ds.data_vars)[0]

                ds[target_var].isel(time=0).plot(ax=ax)
                st.pyplot(fig)

        except Exception as e:
            st.error(f"Ошибка: {e}")