import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import re
import earthaccess
import gzip
import shutil

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ IONEX")

if st.button("🚀 Построить корректную карту"):
    try:
        # Загрузка и распаковка
        results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', temporal=('2026-05-20', '2026-05-31'),
                                          count=1)
        session = earthaccess.login(persist=True).get_session()
        response = session.get(results[0].data_links()[0], stream=True)

        with open("data.ionex.gz", 'wb') as f:
            f.write(response.content)
        with gzip.open("data.ionex.gz", 'rb') as f_in:
            with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)

        # Парсинг
        with open("data.ionex", 'r', encoding='ascii', errors='ignore') as f:
            content = f.read()

        match = re.search(r"START OF TEC MAP(.*?)END OF TEC MAP", content, re.DOTALL)
        if match:
            # Извлекаем числа
            data = np.array([float(x) for x in re.findall(r"[-+]?\d*\.\d+|\d+", match.group(1))])
            data[data >= 9000] = np.nan

            # РЕШАЮЩИЙ ШАГ: порядок [широта (71), долгота (73)]
            # Транспонирование .T и переворот flipud исправляют порядок считывания
            if len(data) >= 5183:
                grid = data[:5183].reshape((71, 73)).T
                grid = np.flipud(grid)

                fig, ax = plt.subplots(figsize=(12, 6))
                im = ax.imshow(grid, cmap='jet', aspect='auto',
                               extent=[-180, 180, -87.5, 87.5], origin='lower')

                plt.colorbar(im, label='VTEC (0.1 TECU)')
                ax.set_xlabel("Долгота")
                ax.set_ylabel("Широта")
                st.pyplot(fig)
                st.success("Карта построена!")
            else:
                st.error("Данных недостаточно.")
        else:
            st.error("Блок данных не найден.")
    except Exception as e:
        st.error(f"Ошибка: {e}")