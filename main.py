import streamlit as st
import earthaccess
import os
import gzip
import shutil
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="IonoSeis AI | Expert", layout="wide")
st.title("🛰 IonoSeis AI: Анализ ионосферных аномалий")

DATA_DIR = "./data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def get_and_unpack_data():
    short_name = 'GNSS_IGS_AC_ion_VTEC_comp'
    earthaccess.login(strategy="interactive")
    results = earthaccess.search_data(short_name=short_name)
    if not results: return None

    files = earthaccess.download(results[-1], DATA_DIR)
    file_path = files[0]

    unzipped_path = file_path.replace('.gz', '')
    with gzip.open(file_path, 'rb') as f_in:
        with open(unzipped_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    return unzipped_path


if st.button("🚀 Запустить научный анализ"):
    with st.spinner("Извлечение данных и статистическая обработка..."):
        try:
            path = get_and_unpack_data()
            if path:
                tec_values = []
                with open(path, 'r') as f:
                    in_map = False
                    for line in f:
                        if "START OF TEC MAP" in line: in_map = True
                        if "END OF TEC MAP" in line: in_map = False
                        if in_map and not any(c.isalpha() for c in line):
                            for p in line.split():
                                val = float(p)
                                if val < 9999: tec_values.append(val / 10.0)

                # Статистический анализ
                if tec_values:
                    data = np.array(tec_values[::50])  # Берем выборку
                    moving_avg = np.convolve(data, np.ones(10) / 10, mode='same')
                    threshold = np.std(data) * 2  # Порог 2 сигмы

                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.plot(data, color='gray', alpha=0.5, label="Raw VTEC")
                    ax.plot(moving_avg, color='blue', label="Норма (Trend)")
                    ax.fill_between(range(len(data)), moving_avg - threshold, moving_avg + threshold,
                                    color='green', alpha=0.2, label="Зона нормы")

                    # Поиск аномалий
                    anomalies = np.where(np.abs(data - moving_avg) > threshold)[0]
                    ax.scatter(anomalies, data[anomalies], color='red', label="АНОМАЛИЯ!")

                    ax.set_title("Мониторинг предвестников землетрясений")
                    ax.legend()
                    st.pyplot(fig)

                    if len(anomalies) > 0:
                        st.warning("⚠️ Внимание: Обнаружены ионосферные аномалии!")
                    else:
                        st.success("Ситуация в норме, аномалий не обнаружено.")
            else:
                st.error("Данные не найдены.")
        except Exception as e:
            st.error(f"Ошибка: {e}")
