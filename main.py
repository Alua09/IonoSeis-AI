import streamlit as st
import pandas as pd
import requests
import time

# Использование заголовка User-Agent, чтобы серверы не видели в нас "бота"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def get_data_with_fallback(url):
    try:
        # Запрос через прокси-агрегатор
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        # Пауза перед второй попыткой (если сервер "занят")
        time.sleep(2)
        return None

# В коде вашего приложения замените вызовы NOAA на:
# data = get_data_with_fallback("https://api.allorigins.win/get?url=https://services.swpc.noaa.gov/products/noaa-k-index.json")