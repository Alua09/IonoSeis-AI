import json
from datetime import datetime

# Функция для имитации получения реальных данных
def update_data():
    # Здесь в будущем будет ваш парсинг NASA/IGS
    data = {
        "Алматы": 16.5,
        "Бишкек": 16.2,
        "Токио": 18.1,
        "Тайвань (Хуалянь)": 17.8,
        "Стамбул": 15.5
    }
    with open('vtec_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f)
    print("Данные успешно обновлены в vtec_data.json")

if __name__ == "__main__":
    update_data()