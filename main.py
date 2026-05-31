import streamlit as st
import georinex as gr
import matplotlib.pyplot as plt
import requests
import gzip
import shutil
import os

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ IONEX")

# Ссылка на файл
url = "https://cddis.nasa.gov/archive/gnss/products/ionex/2026/150/casg1500.26i.Z"

if st.button("🚀 Загрузить и обработать IONEX"):
    with st.spinner("Скачивание и распаковка..."):
        try:
            # 1. Скачиваем файл
            local_filename = "casg1500.26i.Z"
            response = requests.get(url, stream=True)
            with open(local_filename, 'wb') as f:
                shutil.copyfileobj(response.raw, f)

            # 2. Распаковка (формат .Z требует 'uncompress' или сторонних утилит,
            # но часто в таких именах скрыт обычный gzip)
            # Если gzip не берет, попробуем переименовать или прочитать как текст
            final_path = "data.ionex"

            # Попытка распаковать как gzip
            try:
                with gzip.open(local_filename, 'rb') as f_in:
                    with open(final_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            except:
                # Если файл не сжат gzip, просто переименуем для georinex
                shutil.copy(local_filename, final_path)

            # 3. Чтение через georinex (лучший инструмент для IONEX)
            ds = gr.load(final_path)

            st.success("Данные успешно считаны!")

            fig, ax = plt.subplots(figsize=(10, 6))
            if 'TEC' in ds:
                ds['TEC'].isel(time=0).plot(ax=ax)
                st.pyplot(fig)
            else:
                st.write("Найдена структура данных:", ds)

        except Exception as e:
            st.error(f"Ошибка обработки: {e}")
            st.info("Возможно, формат файла требует авторизации NASA Earthdata. Убедитесь, что ваш токен настроен.")