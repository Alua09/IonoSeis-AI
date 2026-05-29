import streamlit as st
import earthaccess
import os
import gzip
import shutil
import matplotlib.pyplot as plt
import numpy as np

# Настройка страницы
st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ ионосферных аномалий")

# Автоматическое создание папки для данных
DATA_DIR = "./data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def get_and_unpack_data():
    short_name = 'GNSS_IGS_AC_ion_VTEC_comp'
    
    # Используем интерактивный вход: при первом запуске в терминале 
    # нужно будет один раз ввести логин/пароль NASA. Это самый надежный способ.
    earthaccess.login(strategy="interactive")
        
    results = earthaccess.search_data(short_name=short_name)
    if not results: return None
    
    # Скачиваем последний доступный файл
    files = earthaccess.download(results[-1], DATA_DIR)
    file_path = files[0]
    
    # Распаковка
    unzipped_path = file_path.replace('.gz', '')
    with gzip.open(file_path, 'rb') as f_in:
        with open(unzipped_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    return unzipped_path

if st.button("🚀 Запустить научный анализ"):
    with st.spinner("Извлечение и обработка данных..."):
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
                                try:
                                    val = float(p)
                                    if val < 9999: tec_values.append(val / 10.0)
                                except: continue
                
                if tec_values:
                    data = np.array(tec_values)
                    # Вычисляем скользящее среднее (фон)
                    moving_avg = np.convolve(data, np.ones(50)/50, mode='same')
                    threshold = np.std(data) * 2
                    
                    # Визуализация (последние 1000 точек для наглядности)
                    fig, ax = plt.subplots(figsize=(8, 4))
                    idx = np.arange(len(data))[-1000:]
                    
                    ax.plot(idx, data[-1000:], color='gray', alpha=0.5, label="VTEC")
                    ax.plot(idx, moving_avg[-1000:], color='blue', label="Фоновый тренд")
                    ax.fill_between(idx, moving_avg[-1000:] - threshold, moving_avg[-1000:] + threshold, 
                                    color='green', alpha=0.2)
                    
                    # Отметка аномалий
                    anomalies = np.where(np.abs(data - moving_avg) > threshold)[0]
                    anomalies = anomalies[anomalies > (len(data) - 1000)]
                    ax.scatter(anomalies, data[anomalies], color='red', s=15, label="Аномалия")
                    
                    ax.set_title("Мониторинг ионосферных предвестников")
                    ax.legend(loc='upper right', fontsize='small')
                    plt.tight_layout()
                    st.pyplot(fig)
                    
                    if len(anomalies) > 0:
                        st.warning("⚠️ Обнаружены ионосферные аномалии!")
                    else:
                        st.success("Ионосфера в спокойном состоянии.")
            else:
                st.error("Данные не найдены.")
        except Exception as e:
            st.error(f"Ошибка: {e}")
