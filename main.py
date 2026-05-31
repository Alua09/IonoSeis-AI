import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import earthaccess
import gzip
import shutil

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ IONEX")

if st.button("🚀 Построить карту"):
    try:
        # 1. Загрузка
        results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', temporal=('2026-05-20', '2026-05-31'),
                                          count=1)
        session = earthaccess.login(persist=True).get_session()
        response = session.get(results[0].data_links()[0], stream=True)
        with open("data.ionex.gz", 'wb') as f:
            f.write(response.content)
        with gzip.open("data.ionex.gz", 'rb') as f_in:
            with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)

        # 2. Прямой парсинг строк
        tec_values = []
        in_block = False
        with open("data.ionex", 'r') as f:
            for line in f:
                if 'START OF TEC MAP' in line:
                    in_block = True
                elif 'END OF TEC MAP' in line:
                    in_block = False
                elif in_block:
                    # Берем первые 60 символов, где строго лежат данные TEC
                    parts = line[:60].split()
                    for p in parts:
                        try:
                            val = float(p)
                            if val < 9000: tec_values.append(val)
                        except:
                            continue

        # 3. Визуализация
        data = np.array(tec_values)
        if len(data) >= 5183:
            # Формируем сетку 71x73
            grid = data[:5183].reshape((71, 73))

            # Если карта всё равно выглядит как гармошка,
            # поменяйте местами (71, 73) на (73, 71) ниже:
            grid = grid.T

            fig, ax = plt.subplots(figsize=(10, 5))
            im = ax.imshow(grid, cmap='jet', origin='lower', aspect='auto',
                           extent=[-180, 180, -87.5, 87.5])

            plt.colorbar(im, label='VTEC (0.1 TECU)')
            ax.set_xlabel("Долгота")
            ax.set_ylabel("Широта")
            st.pyplot(fig)
            st.success("Готово!")
        else:
            st.error(f"Найдено {len(data)} точек. Нужно 5183.")

    except Exception as e:
        st.error(f"Ошибка: {e}")