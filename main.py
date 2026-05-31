import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import earthaccess
import gzip
import shutil

st.set_page_config(layout="wide")
st.title("🛰 IonoSeis AI: Финальный Парсер")

if st.button("🚀 Построить карту"):
    try:
        # 1. Скачивание
        results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', temporal=('2026-05-20', '2026-05-31'),
                                          count=1)
        session = earthaccess.login(persist=True).get_session()
        response = session.get(results[0].data_links()[0], stream=True)
        with open("data.ionex.gz", 'wb') as f:
            f.write(response.content)
        with gzip.open("data.ionex.gz", 'rb') as f_in:
            with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)

        # 2. Чтение данных
        tec_values = []
        with open("data.ionex", 'r') as f:
            in_block = False
            for line in f:
                if 'START OF TEC MAP' in line:
                    in_block = True
                elif 'END OF TEC MAP' in line:
                    in_block = False
                elif in_block and 'LAT/LON1/LON2' not in line:
                    # Чистим строку и берем только числа
                    parts = line.split()
                    for p in parts:
                        try:
                            val = float(p)
                            if val < 9000: tec_values.append(val)
                        except:
                            continue

        # 3. Сборка сетки (NRCAN GIM это 71 широта на 73 долготы)
        # Мы преобразуем список в массив и сразу меняем ориентацию
        data = np.array(tec_values)
        if len(data) >= 5183:
            # Магия здесь: чтобы убрать полосы, мы используем reshape 71x73
            # и транспонируем, а затем разворачиваем, если надо
            grid = data[:5183].reshape((71, 73))

            # Если полосы остались, значит массив надо перевернуть
            # Попробуйте этот вариант:
            final_grid = np.flipud(grid.T)

            fig, ax = plt.subplots(figsize=(10, 5))
            # origin='lower' + extent = правильная география
            im = ax.imshow(final_grid, cmap='jet', origin='lower', aspect='auto',
                           extent=[-180, 180, -87.5, 87.5])

            plt.colorbar(im, label='VTEC')
            st.pyplot(fig)
        else:
            st.error(f"Данных не хватает: {len(data)}. Файл битый.")

    except Exception as e:
        st.error(f"Ошибка: {e}")