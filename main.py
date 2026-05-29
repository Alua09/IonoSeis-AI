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

# Автоматическое определение пути к папке данных
DATA_DIR = os.path.join(os.getcwd(), "data")

def get_and_unpack_data():
    # Создаем папку, если её нет
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    short_name = 'GNSS_IGS_AC_ion_VTEC_comp'
    
    # Интерактивная авторизация - самый стабильный метод для локального запуска
    st.write("🔄 Подключение к архивам NASA...")
    earthaccess.login(strategy="interactive")
        
    st.write("🔍 Поиск и скачивание данных...")
    results = earthaccess.search_data(short_name=short_name)
    if not results: return None
    
    files = earthaccess.download(results[-1], DATA_DIR)
    file_path = files[0]
    
    # Распаковка файла
    unzipped_path = file_path.replace('.gz', '')
    with gzip.open(file_path, 'rb') as f_in:
        with open(unzipped_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    return unzipped_path

if st.button("🚀 Запустить научный анализ"):
    with st.spinner("Пожалуйста, подождите. Идет обработка данных..."):
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
                    # Статистический расчет
                    moving_avg = np.convolve(data, np.ones(50)/50, mode='same')
                    threshold = np.std(data) * 2
                    
                    # Визуализация
                    fig, ax = plt.subplots(figsize=(10, 5))
                    idx = np.arange(len(data))[-1000:]
                    
                    ax.plot(idx, data[-1000:], color='gray', alpha=0.5, label="VTEC (Данные)")
                    ax.plot(idx, moving_avg[-1000:], color='blue', label="Фоновый тренд")
                    ax.fill_between(idx, moving_avg[-1000:] - threshold, moving_avg[-1000:] + threshold, 
                                    color='green', alpha=0.2, label="Зона нормы")
                    
                    anomalies = np.where(np.abs(data - moving_avg) > threshold)[0]
                    anomalies = anomalies[anomalies > (len(data) - 1000)]
                    ax.scatter(anomalies, data[anomalies], color='red', s=15, label="Аномалия")
                    
                    ax.set_title("Мониторинг предвестников землетрясений")
                    ax.legend()
                    st.pyplot(fig)
                    
                    if len(anomalies) > 0:
                        st.warning("⚠️ Внимание: Обнаружены ионосферные аномалии!")
                    else:
                        st.success("Ионосферный фон в пределах нормы.")
            else:
                st.error("Данные не найдены.")
        except Exception as e:
            st.error(f"Произошла ошибка при обработке: {e}")
