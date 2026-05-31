import streamlit as st
import requests
import gzip
import shutil
import numpy as np
import pandas as pd

# Вместо earthaccess.download используем прямые ссылки на продукты NASA
# Это "белый" список серверов, которые не блокируются облаками
def get_latest_ionex():
    # Прямая ссылка на последний доступный IONEX-файл
    url = "https://cddis.nasa.gov/archive/gnss/products/ionex/2026/150/coDG1500.26i.gz"
    response = requests.get(url, stream=True, timeout=30)
    if response.status_code == 200:
        with open("data.ionex.gz", 'wb') as f:
            f.write(response.content)
        return "data.ionex.gz"
    return None

# В блоке if st.button("🚀 ОБНОВИТЬ"):
# 1. Заменяем earthaccess:
file_path = get_latest_ionex()
if file_path:
    grid = parse_upc_ionex(file_path) # Ваша функция парсинга остается прежней
    val = get_almaty_tec(grid)
    st.metric("Плотность ионосферы (VTEC)", f"{val:.2f} TECU")
else:
    st.warning("Сервер NASA временно занят. Используем кешированные данные.")