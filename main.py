import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import subprocess, os, re, requests
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="IonoSeis AI")
st.title("🛰 IonoSeis AI: Анализ")


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
    vals = [float(x) for x in re.findall(r'\d+\.\d+', content)]
    data = np.array(vals)
    if data.size < 5000: raise ValueError("Мало данных")
    return data[:5183].reshape((71, 73))


if st.button("🚀 ЗАПУСК МОНИТОРИНГА"):
    try:
        # Безопасный запрос данных
        try:
            r = requests.get("https://services.swpc.noaa.gov/products/noaa-k-index.json", timeout=5)
            kp = [float(x[1]) for x in r.json()[1:][-20:]] if r.status_code == 200 else [0] * 20
        except:
            kp = [0] * 20

        earthaccess.login(strategy="netrc")
        results = earthaccess.search_data(short_name='GNSS_IGS_AC_ion_VTEC_comp', count=7)
        paths = earthaccess.download(results, ".")

        a, t = [], []
        for f in paths:
            try:
                g = parse_ionex_robust(f)
                a.append(g[int((43.2 + 87.5) / 2.5), int((76.9 + 180) / 5.0)])
                t.append(g[int((35.6 + 87.5) / 2.5), int((139.6 + 180) / 5.0)])
            except:
                continue

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8))
        ax1.plot(a, color='green', marker='o');
        ax1.set_title("Алматы VTEC")
        ax2.plot(t, color='blue', marker='s');
        ax2.set_title("Токио VTEC")
        ax3.plot(kp, color='red', marker='^');
        ax3.set_title("КП-индекс")
        for ax in [ax1, ax2, ax3]: ax.grid(True)
        st.pyplot(fig)
        st.success("Готово!")
    except Exception as e:
        st.error(f"Ошибка: {e}")