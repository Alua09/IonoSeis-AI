import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import gzip
import shutil
import earthaccess
import requests

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ IONEX")

# Инициализация сессии
try:
    auth = earthaccess.login(persist=True)
    session = auth.get_session()
except Exception as e:
    st.error(f"Ошибка авторизации: {e}")
    st.stop()

if st.button("🚀 Загрузить и визуализировать данные"):
    with st.spinner("Работаем..."):
        try:
            # Поиск актуального файла
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                temporal=('2026-05-20', '2026-05-31'),
                count=1
            )

            if not results:
                st.error("Данные не найдены.")
            else:
                data_url = results[0].data_links()[0]

                # Скачивание
                response = session.get(data_url, stream=True)
                local_filename = "data.ionex.gz"
                with open(local_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # Распаковка
                final_path = "data.ionex"
                with gzip.open(local_filename, 'rb') as f_in:
                    with open(final_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                # Парсинг данных вручную (ищем TEC-блоки)
                tec_data = []
                with open(final_path, 'r', encoding='ascii', errors='ignore') as f:
                    for line in f:
                        # В файлах IONEX данные VTEC идут после меток 'TEC'
                        if 'TEC' in line and '.' in line and 'RMS' not in line:
                            parts = [float(x) for x in line.split() if x.replace('.', '', 1).replace('-', '').isdigit()]
                            tec_data.extend(parts)

                # Визуализация
                if len(tec_data) > 0:
                    # Преобразуем в массив (размерность 71x73 стандартная для многих GIM)
                    data_array = np.array(tec_data[:5183]).reshape((71, 73))

                    fig, ax = plt.subplots(figsize=(10, 6))
                    im = ax.imshow(data_array, cmap='inferno', aspect='auto')
                    plt.colorbar(im, label='VTEC (TECU)')
                    st.pyplot(fig)
                    st.success("Визуализация построена!")
                else:
                    st.error("Не удалось распарсить данные. Файл пуст или формат изменился.")

        except Exception as e:
            st.error(f"Ошибка: {e}")