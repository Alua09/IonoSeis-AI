import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import requests
import gzip
import shutil
import earthaccess

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ ионосферных данных")

# 1. Авторизация
try:
    auth = earthaccess.login(persist=True)
    session = auth.get_session()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}")
    st.stop()

if st.button("🚀 Найти и проанализировать данные"):
    with st.spinner("Поиск и обработка..."):
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
                st.write(f"Загрузка файла: {data_url}")

                # 3. Скачивание
                response = session.get(data_url, stream=True)
                local_filename = "data.inx.gz"
                with open(local_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # 4. Распаковка
                final_path = "data.inx"
                with gzip.open(local_filename, 'rb') as f_in:
                    with open(final_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # 5. Чтение и визуализация
                ds = xr.open_dataset(final_path)
                st.success("Данные успешно считаны!")

                st.write("Структура данных:", ds)

                fig, ax = plt.subplots(figsize=(10, 6))
                # Пробуем отрисовать переменную TEC, если она есть
                if 'TEC' in ds:
                    ds['TEC'].isel(time=0).plot(ax=ax)
                    st.pyplot(fig)
                else:
                    st.warning("Переменная 'TEC' не найдена. Проверьте имена переменных в выводе выше.")

        except Exception as e:
            st.error(f"Ошибка: {e}")