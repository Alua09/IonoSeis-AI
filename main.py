import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import subprocess, os, re, requests
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis: Профессиональный мониторинг")
st.title("🛰 IonoSeis AI: Многослойный мониторинг")


# --- ПАРСЕР ---
def parse_ionex_robust(file_path):
    path_str = str(file_path)
    if path_str.endswith('.Z'):
        subprocess.run(["uncompress", "-f", path_str], check=False)
        path_str = path_str.replace(".Z", "")
    elif path_str.endswith('.gz'):
        subprocess.run(["gunzip", "-f", path_str], check=False)
        path_str = path_str.replace(".gz", "")

    with open(path_str, 'r', errors='ignore') as f:
        content = f.read()

    # Ищем только позитивные значения (TEC не бывает отрицательным)
    vals = [float(x) for x in re.findall(r'\d+\.\d+', content)]
    data = np.array(vals)
    if data.size < 5000: raise ValueError("Мало данных")
    return data[:5183].reshape((71, 73))


# --- ОСНОВНАЯ ЛОГИКА ---
if st.button("🚀 ОБНОВИТЬ СЕЙСМО-ИОНОСФЕРНУЮ КАРТУ"):
    try:
        # 1. КП-индекс (мониторинг магнитных бурь)
        kp_data = requests.get("https://services.swpc.noaa.gov/products/noaa-k-index.json").json()
        kp_values = [float(x[1]) for x in kp_data[1:][-20:]]  # последние 20 записей

        # 2. Поиск данных NASA
        earthaccess.login(strategy="netrc")
        results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', count=7)
        paths = earthaccess.download(results, ".")

        almaty, tokyo = [], []
        for f in paths:
            try:
                g = parse_ionex_robust(f)
                almaty.append(g[int((43.2 + 87.5) / 2.5), int((76.9 + 180) / 5.0)])
                tokyo.append(g[int((35.6 + 87.5) / 2.5), int((139.6 + 180) / 5.0)])
            except:
                continue

        # 3. Визуализация (3 отдельных графика)
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

        ax1.plot(almaty, color='green', marker='o', label='VTEC Алматы')
        ax1.set_title("Алматы: Мониторинг")

        ax2.plot(tokyo, color='blue', marker='s', label='VTEC Токио')
        ax2.set_title("Токио: Мониторинг")

        ax3.plot(kp_values, color='red', marker='^', label='КП-индекс (Солнце)')
        ax3.set_title("Уровень магнитных бурь (K-index > 5 = ШУМ)")

        for ax in [ax1, ax2, ax3]: ax.grid(True)
        st.pyplot(fig)

        st.info(
            "Анализ завершен. Сверяйте скачки VTEC с КП-индексом. Если КП стабилен, а VTEC прыгает — это повод для внимания.")

    except Exception as e:
        st.error(f"Ошибка системы: {e}")