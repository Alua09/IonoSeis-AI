import json
import requests
from datetime import datetime


def update_data():
    # Эмуляция получения данных VTEC (в будущем — парсинг IONEX)
    vtec_base = 16.5

    data = {
        "Алматы": vtec_base,
        "Бишкек": vtec_base - 0.3,
        "Токио": 18.2,
        "Тайвань (Хуалянь)": 17.5,
        "Стамбул": 15.1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open('vtec_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Данные обновлены: {data['timestamp']}")


if __name__ == "__main__":
    update_data()