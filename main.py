import streamlit as st
import earthaccess
import os
import gzip
import shutil
import matplotlib.pyplot as plt
import xarray as xr

# Устанавливаем соединение с NASA (если нужно, он подхватит ваш .netrc)
earthaccess.login(strategy="interactive")

st.title("🛰 IonoSeis AI: Анализ данных IGS")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)


def get_specific_data():
    # Используем тот самый короткий набор данных, который мы определили как рабочий
    short_name = 'GNSS_IGS_AC_ion_VTEC_comp'

    # Ищем результаты
    results = earthaccess.search_data(short_name=short_name, count=5)

    if not results:
        return None, "Файлы не найдены в базе."

    # Берем последний доступный файл из списка, который мы уже проверяли
    target_file = results[-1]
    files = earthaccess.download(target_file, DATA_DIR)

    return files[0], None


if st.button("🚀 Анализировать данные IGS"):
    with st.spinner("Загрузка из базы..."):
        path, error = get_specific_data()
        if error:
            st.error(error)
        else:
            try:
                # Распаковка, если файл сжат
                unpacked = path.replace('.gz', '')
                if not os.path.exists(unpacked):
                    with gzip.open(path, 'rb') as f_in:
                        with open(unpacked, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)

                # Чтение через xarray
                ds = xr.open_dataset(unpacked)
                st.write("Данные загружены:", ds)

                # Визуализация
                fig, ax = plt.subplots()
                # Предполагаем структуру данных, которую мы видели ранее
                ds['TEC'].isel(time=0).plot(ax=ax)
                st.pyplot(fig)
            except Exception as e:
                st.error(f"Ошибка при чтении файла: {e}")