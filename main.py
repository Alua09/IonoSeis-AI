import streamlit as st
import earthaccess
import georinex as gr
import matplotlib.pyplot as plt
import xarray as xr
from datetime import datetime, timedelta
import gzip
import shutil

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ данных")

try:
    earthaccess.login()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}")

if st.button("🚀 Анализировать данные"):
    with st.spinner("Поиск и загрузка..."):
        try:
            # 1. Поиск
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                count=1
            )

            if not results:
                st.error("Данные не найдены. Попробуйте изменить параметры поиска.")
            else:
                # 2. Скачивание
                files = earthaccess.download(results, "data")

                # ЗАЩИТА: проверяем, что список не пуст
                if not files:
                    st.error("Файлы не были загружены (список пуст).")
                else:
                    raw_path = str(files[0])
                    st.write(f"Файл загружен: {raw_path}")

                    # 3. Распаковка
                    unpacked_path = raw_path + ".uncompressed"
                    with gzip.open(raw_path, 'rb') as f_in:
                        with open(unpacked_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    # 4. Чтение
                    try:
                        # Попробуем через xarray, так как он более универсален для .INX файлов
                        ds = xr.open_dataset(unpacked_path)
                        st.success("Данные успешно считаны!")

                        fig, ax = plt.subplots(figsize=(10, 6))
                        if 'TEC' in ds:
                            ds['TEC'].isel(time=0).plot(ax=ax)
                            st.pyplot(fig)
                        else:
                            st.write("Структура данных:", ds)
                    except Exception as e:
                        st.error(f"Ошибка чтения файла: {e}")

        except Exception as e:
            st.error(f"Общая ошибка: {e}")