import streamlit as st
import earthaccess
import numpy as np
import matplotlib.pyplot as plt
import requests
import gzip
import shutil
import os
import pandas as pd
from datetime import datetime, timedelta
import subprocess # Для вызова системных команд распаковки, если есть

# ... (остальной код остается тем же, меняем только safe_extract)

def safe_extract(file_path):
    """Максимально надежный метод: пытается gzip, если нет — пробует uncompress, если нет — копирует как есть"""
    try:
        # Пробуем через gzip
        with gzip.open(file_path, 'rb') as f_in:
            with open("data.ionex", 'wb') as f_out: shutil.copyfileobj(f_in, f_out)
    except:
        # Если не вышло, пробуем через системную команду uncompress (если доступна)
        try:
            subprocess.run(["uncompress", file_path], check=True)
            # После распаковки файл должен изменить имя на .ionex или похожее
            # В данном случае просто переименуем его, если он есть
            uncompressed_file = file_path.replace('.Z', '')
            shutil.move(uncompressed_file, "data.ionex")
        except:
            # Если всё совсем плохо, просто копируем файл (иногда он уже распакован)
            shutil.copyfile(file_path, "data.ionex")