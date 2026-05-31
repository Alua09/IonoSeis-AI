import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import re
import earthaccess
import gzip
import shutil

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ ионосферы")

if st.button("🚀 Построить карту VTEC"):
    try:
        # Авторизация и поиск данных
        results = earthaccess.search_data(
            short_name='GNSS_IGS_AC_ion_VTEC_comp',
            temporal=('2026-05-20', '2026-05-31'),
            count=1
        )
        data_url = results[0].data_links()[0]

        session = earthaccess.login(persist=True).get_session()
        response = session.get(data_url, stream=True)

        with open("data.ionex.gz", 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        with gzip.open("data.ionex.gz", 'rb') as f_in:
            with open("data.ionex", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Парсинг
        with open("data.ionex", 'r', encoding='ascii', errors='ignore') as f:
            content = f.read()

        match = re.search(r"START OF TEC MAP(.*?)END OF TEC MAP", content, re.DOTALL)
        if match:
            block = match.group(1)
            # Извлекаем все числа
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", block)
            data = np.array([float(n) for n in numbers])

            # Фильтр пустых значений
            data[data >= 9000] = np.nan

            # ПРАВИЛЬНАЯ РАБОТА С СЕТКОЙ:
            # 71 широта, 73 долгота. Используем transpose (.T) для правильного отображения.
            if len(data) >= 5183:
                # Берем ровно 71*73 значений и транспонируем
                grid = data[:5183].reshape((71, 73)).T

                # Поворачиваем для корректной ориентации (Север сверху)
                grid = np.flipud(grid)

                fig, ax = plt.subplots(figsize=(12, 6))

                # extent=[-180, 180, -87.5, 87.5] связывает данные с координатами
                im = ax.imshow(grid, cmap='jet', aspect='auto',
                               extent=[-180, 180, -87.5, 87.5], origin='lower')

                plt.colorbar(im, label='VTEC (0.1 TECU)')
                ax.set_xlabel("Долгота")
                ax.set_ylabel("Широта")
                ax.set_title("Глобальная карта VTEC")

                st.pyplot(fig)
                st.success("Карта построена!")
            else:
                st.error("Ошибка структуры данных.")
        else:
            st.error("Блок данных не найден.")

    except Exception as e:
        st.error(f"Ошибка: {e}")