import pandas as pd
import numpy as np
import requests
import gzip
import shutil
from datetime import datetime, timedelta


def get_latest_ionex_data(lat, lon):
    """
    Эта функция качает свежий файл, распаковывает его и достает VTEC 
    для конкретной точки. Это ядро вашей системы.
    """
    # 1. Формируем URL для последних данных IGS
    date_str = datetime.now().strftime("%y%j")  # Формат для IGS (год + день года)
    url = f"https://cddis.nasa.gov/archive/gnss/products/ionex/{datetime.now().year}/001/codg{date_str}.00i.Z"

    # 2. Скачивание с обработкой ошибок
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None  # Данные еще не загружены на сервер

        with open("temp.Z", "wb") as f:
            f.write(response.content)
        # Распаковка (через системную команду)
        import subprocess
        subprocess.run(["uncompress", "-f", "temp.Z"])

        # 3. Парсинг (достаем только цифры из файла)
        with open(f"codg{date_str}.00i", 'r', errors='ignore') as f:
            content = f.read()
            # Логика извлечения VTEC (сетка 71x73)
            # ... (здесь будет логика извлечения чисел) ...
            return vtec_value

    except Exception as e:
        print(f"Ошибка получения данных: {e}")
        return None