import earthaccess
import xarray as xr
from datetime import datetime, timedelta
import os


def download_nasa_data():
    # Авторизация (использует переменные окружения, которые мы настроили)
    earthaccess.login(strategy="netrc")

    # Ищем данные GIM IONEX за последние 3 дня
    results = earthaccess.search_data(
        short_name='GIM_IONEX',
        temporal=(datetime.now() - timedelta(days=3), datetime.now())
    )

    # Скачиваем последний доступный файл
    files = earthaccess.download(results[-1], "./data")
    return files[0]  # Возвращает путь к скачанному файлу


if __name__ == "__main__":
    download_nasa_data()