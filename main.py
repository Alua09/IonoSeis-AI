import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import re
import earthaccess
import gzip
import shutil

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Итоговая карта VTEC")

if st.button("🚀 Построить корректную карту"):
    try:
        # 1. Загрузка
        results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', temporal=('2026-05-20', '2026-05-31'),
                                          count=1)
        data_url = results[0].data_links()[0]

        # 2. Скачивание и распаковка
        session = earthaccess.login(persist=True).get_session()
        response = session.get(data_url, stream=True)
        with open("data.ionex.gz", 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        with gzip.open("data.ionex.gz", 'rb') as f_in:
            with open("data.ionex", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # 3. Парсинг
        with open("data.ionex", 'r', encoding='ascii', errors='ignore') as f:
            content = f.read()

        match = re.search(r"START OF TEC MAP(.*?)END OF TEC MAP", content, re.DOTALL)
        if match:
            block = match.group(1)
            # Извлекаем все числа
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", block)
            data = np.array([float(n) for n in numbers])

            # Фильтр "пустых" значений (9999)
            data[data >= 9000] = np.nan

            # 4. Формирование сетки
            # Если 5183 точки (71*73), меняем форму и делаем транспонирование
            if len(data) >= 5183:
                grid = data[:5183].reshape((71, 73))

                # Поворот и отражение для корректного отображения координат
                grid = np.flipud(grid)

                fig, ax = plt.subplots(figsize=(12, 6))
                im = ax.imshow(grid, cmap='jet', aspect='auto',
                               extent=[-180, 180, -87.5, 87.5])

                plt.colorbar(im, label='VTEC (0.1 TECU)')
                ax.set_xlabel("Долгота (градусы)")
                ax.set_ylabel("Широта (градусы)")
                ax.set_title("Глобальная карта ионосферы (NRCAN GIM)")
                st.pyplot(fig)
            else:
                st.error("Ошибка размерности данных.")
        else:
            st.error("Блок данных не найден.")

    except Exception as e:
        st.error(f"Ошибка: {e}")