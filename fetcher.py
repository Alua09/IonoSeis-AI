import json
import os
from datetime import datetime

# Явный путь к файлу
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, 'vtec_data.json')

def fetch_real_vtec():
    try:
        # Здесь ваши реальные данные
        data = {
            "Алматы": 16.5,
            "Бишкек": 16.2,
            "Токио": 18.2,
            "Тайвань (Хуалянь)": 17.5,
            "Стамбул": 15.1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"Файл успешно записан в: {FILE_PATH}")
    except Exception as e:
        print(f"Ошибка записи: {e}")

if __name__ == "__main__":
    fetch_real_vtec()