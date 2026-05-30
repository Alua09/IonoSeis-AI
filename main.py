import streamlit as st
import earthaccess
import georinex as gr
import matplotlib.pyplot as plt
import os

st.title("🛰 IonoSeis AI: Анализ IONEX")

earthaccess.login(strategy="netrc")

if st.button("🚀 Анализировать данные"):
    with st.spinner("Загрузка данных..."):
        try:
            # Ищем данные за последние дни
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                count=1
            )

            # Скачиваем
            files = earthaccess.download(results, "data")
            path = files[0]

            # Используем georinex для чтения IONEX
            # Он сам распознает структуру файла
            ds = gr.load(path)

            # Визуализация TEC (Total Electron Content)
            fig, ax = plt.subplots()
            # В IONEX данные часто хранятся в переменной TEC
            ds['TEC'].plot(ax=ax)

            st.pyplot(fig)
            st.success("Данные успешно визуализированы!")

        except Exception as e:
            st.error(f"Ошибка при обработке файла: {e}")