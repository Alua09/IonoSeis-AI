import streamlit as st
import earthaccess
import numpy as np
from datetime import datetime, timedelta
import os

# Авторизация (использует netrc, созданный вами ранее)
earthaccess.login(strategy="netrc")

st.title("🛰 IonoSeis AI: Глобальный поисковик")

if st.button("🚀 НАЙТИ ЛЮБЫЕ ДАННЫЕ В АРХИВЕ"):
    with st.spinner("Сканирую архивы NASA..."):
        try:
            # Ищем во всех возможных коллекциях IGS за 30 дней
            collections = ['IGS_GIM', 'GNSS_IGS_AC_ion_VTEC_comp', 'GIM_IONEX']
            found_files = []

            for coll in collections:
                results = earthaccess.search_data(
                    short_name=coll,
                    temporal=(datetime.now() - timedelta(days=30), datetime.now()),
                    count=5  # Берем последние 5 файлов
                )
                if results:
                    st.write(f"✅ Найдено в {coll}: {len(results)} файлов")
                    found_files = results
                    break  # Останавливаемся на первой найденной коллекции

            if not found_files:
                st.error("Архив пуст. Проверьте ваш профиль на Earthdata (статус одобрения данных).")
            else:
                # Скачиваем первый найденный
                files = earthaccess.download(found_files[0], "./tmp")
                st.success(f"Успешно скачан файл: {os.path.basename(files[0])}")
                st.write("Теперь данные готовы к парсингу!")

        except Exception as e:
            st.error(f"Ошибка поиска: {e}")