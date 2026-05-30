import streamlit as st
import earthaccess
import georinex as gr
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import subprocess
import os

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ данных")

try:
    earthaccess.login()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}")

if st.button("🚀 Анализировать данные"):
    with st.spinner("Диагностика файла..."):
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

                # Читаем первые 500 байт файла, чтобы увидеть, что там внутри
                with open(raw_path, 'rb') as f:
                    header_sample = f.read(500)

                st.write("Первые 500 байт файла (для диагностики):")
                st.code(header_sample[:200])  # Покажем первые 200 символов

                # Если файл сжат, покажем это
                if header_sample.startswith(b'\x1f\x8b'):
                    st.warning("Файл выглядит как GZIP (бинарный).")
                elif b'IONEX' in header_sample:
                    st.success("Файл содержит сигнатуру IONEX!")
                else:
                    st.error("Файл не содержит ожидаемого заголовка IONEX.")

        except Exception as e:
            st.error(f"Ошибка при чтении: {e}")