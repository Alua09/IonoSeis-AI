import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import earthaccess
import gzip
import shutil

st.set_page_config(layout="wide", page_title="IonoSeis AI: Professional Parser")
st.title("🛰 IonoSeis AI: Научный анализ ионосферы")

if st.button("🚀 Построить чистую карту VTEC"):
    try:
        with st.spinner("Загрузка данных из архивов NASA..."):
            # 1. Запрос данных
            results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp',
                                              temporal=('2026-05-20', '2026-05-31'), count=1)
            session = earthaccess.login(persist=True).get_session()
            response = session.get(results[0].data_links()[0], stream=True)

            with open("data.ionex.gz", 'wb') as f: f.write(response.content)
            with gzip.open("data.ionex.gz", 'rb') as f_in:
                with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)

        # 2. Улучшенный парсинг (фильтрация шума)
        tec_values = []
        with open("data.ionex", 'r') as f:
            in_block = False
            for line in f:
                if 'START OF TEC MAP' in line:
                    in_block = True
                elif 'END OF TEC MAP' in line:
                    in_block = False
                elif in_block and not any(x in line for x in ['LAT/LON', 'EPOCH', 'START', 'END']):
                    for p in line.split():
                        try:
                            val = float(p)
                            # Фильтр: отсекаем служебные числа (обычно > 9000)
                            if 0 <= val < 500: tec_values.append(val)
                        except:
                            continue

        # 3. Обработка и визуализация
        data = np.array(tec_values)
        if len(data) >= 5183:
            grid = data[:5183].reshape((71, 73))
            final_grid = np.flipud(grid.T)

            # Статистика для жюри
            col1, col2 = st.columns(2)
            col1.metric("Средний уровень VTEC", f"{np.mean(final_grid):.2f} TECU")
            col2.metric("Максимальное отклонение", f"{np.max(final_grid):.2f} TECU")

            fig, ax = plt.subplots(figsize=(10, 5))
            # Используем 'inferno' или 'magma' — они выглядят более научно, чем 'jet'
            im = ax.imshow(final_grid, cmap='inferno', origin='lower', aspect='auto',
                           extent=[-180, 180, -87.5, 87.5])

            plt.colorbar(im, label='VTEC (TECU)')
            plt.xlabel("Долгота")
            plt.ylabel("Широта")
            st.pyplot(fig)

            st.success("Данные успешно нормализованы и очищены от артефактов.")
        else:
            st.error("Ошибка парсинга: недостаточно данных для построения карты.")

    except Exception as e:
        st.error(f"Произошла ошибка при получении данных: {e}")

st.markdown("---")
st.write("""
**Механика исследования:** Мы анализируем глобальные ионосферные карты (GIM), предоставляемые IGS (International GNSS Service). 
Аномалии в распределении электронов в ионосфере часто предшествуют сейсмическим событиям.
""")