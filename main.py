import streamlit as st
import earthaccess
import os
import gzip
import shutil
import matplotlib.pyplot as plt
import numpy as np
import random  # Добавили для случайности

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Анализ ионосферных аномалий")

DATA_DIR = os.path.join(os.getcwd(), "data")

def get_and_unpack_data():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    short_name = 'GNSS_IGS_AC_ion_VTEC_comp'
    earthaccess.login(strategy="interactive")
        
    results = earthaccess.search_data(short_name=short_name)
    if not results: return None
    
    # БЕРЕМ СЛУЧАЙНЫЙ ИЗ ПОСЛЕДНИХ 5 ФАЙЛОВ, ЧТОБЫ ДАННЫЕ МЕНЯЛИСЬ
    idx = random.randint(max(0, len(results)-5), len(results)-1)
    files = earthaccess.download(results[idx], DATA_DIR)
    
    file_path = files[0]
    base = os.path.splitext(file_path)[0]
    
    with gzip.open(file_path, 'rb') as f_in:
        with open(base, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    return base

if st.button("🚀 Запустить научный анализ"):
    plt.clf() # Очистка памяти перед рисованием
    with st.spinner("Загрузка актуальных данных..."):
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
                    moving_avg = np.convolve(data, np.ones(50)/50, mode='same')
                    threshold = np.std(data) * 2
                    
                    # ПРИНУДИТЕЛЬНОЕ ИЗМЕНЕНИЕ РАЗМЕРА
                    fig, ax = plt.subplots(figsize=(6, 3), dpi=100)
                    idx = np.arange(len(data))[-1000:]
                    
                    ax.plot(idx, data[-1000:], color='gray', alpha=0.5, label="VTEC")
                    ax.plot(idx, moving_avg[-1000:], color='blue', label="Фон")
                    ax.fill_between(idx, moving_avg[-1000:] - threshold, moving_avg[-1000:] + threshold, color='green', alpha=0.2)
                    
                    anomalies = np.where(np.abs(data - moving_avg) > threshold)[0]
                    anomalies = anomalies[anomalies > (len(data) - 1000)]
                    ax.scatter(anomalies, data[anomalies], color='red', s=10, label="Аномалия")
                    
                    ax.set_title("Мониторинг ионосферы")
                    ax.legend(fontsize='x-small')
                    st.pyplot(fig)
            else: st.error("Нет данных.")
        except Exception as e: st.error(f"Ошибка: {e}")
