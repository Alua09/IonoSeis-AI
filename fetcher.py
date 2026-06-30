import json
import os
import subprocess
from datetime import datetime

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, 'vtec_data.json')


def fetch_real_vtec():
    try:
        # --- СЕКЦИЯ СБОРА ДАННЫХ ---
        # Здесь ваша логика парсинга (заглушка для примера)
        data = {
            "Алматы": 16.5,
            "Бишкек": 16.2,
            "Токио": 18.2,
            "Тайвань (Хуалянь)": 17.5,
            "Стамбул": 15.1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Запись в файл
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"Данные записаны в {FILE_PATH}")

        # --- СЕКЦИЯ АВТОМАТИЗАЦИИ (GIT) ---
        # Добавляем файл, коммитим и пушим в облако
        subprocess.run(["git", "add", "vtec_data.json"], check=True)

        # Коммит с проверкой, есть ли что коммитить (чтобы не было ошибок, если данные те же)
        status = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
        if status.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Auto-update: VTEC data refresh"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print("Данные успешно отправлены в облако (Git Push).")
        else:
            print("Данные не изменились, пропуск Git Push.")

    except Exception as e:
        print(f"Критическая ошибка: {e}")


if __name__ == "__main__":
    fetch_real_vtec()