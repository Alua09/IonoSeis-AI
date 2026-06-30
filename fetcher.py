import json
import requests
from datetime import datetime


def fetch_real_vtec():
    # Имитация запроса к реальному источнику данных
    # Замените этот блок на ваш реальный парсинг IONEX или API
    try:
        # Здесь должен быть ваш код получения данных
        # Пример: response = requests.get("URL_К_ВАШЕМУ_ИСТОЧНИКУ")

        # Для теста "живых" данных
        new_data = {
            "Алматы": 16.8,
            "Бишкек": 16.5,
            "Токио": 18.9,
            "Тайвань (Хуалянь)": 18.2,
            "Стамбул": 15.4,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Записываем только если данные не пустые
        if new_data:
            with open('vtec_data.json', 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False)

    except Exception as e:
        print(f"Ошибка сбора данных: {e}")


if __name__ == "__main__":
    fetch_real_vtec()