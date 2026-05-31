import streamlit as st
import earthaccess
import gzip
import shutil

st.set_page_config(page_title="IonoSeis AI", layout="wide")
st.title("🛰 IonoSeis AI: Диагностика формата")

if st.button("🔍 Показать содержимое файла для анализа"):
    try:
        # Повторяем процесс загрузки
        results = earthaccess.search_data(
            short_name='GNSS_IGS_AC_ion_VTEC_comp',
            temporal=('2026-05-20', '2026-05-31'),
            count=1
        )
        data_url = results[0].data_links()[0]

        # Скачивание и распаковка
        response = earthaccess.get_requests_session().get(data_url, stream=True)
        with open("data.ionex.gz", 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        with gzip.open("data.ionex.gz", 'rb') as f_in:
            with open("data.ionex", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # ЧИТАЕМ И ВЫВОДИМ
        with open("data.ionex", 'r', encoding='ascii', errors='ignore') as f:
            content = f.read(2000)  # Читаем первые 2000 символов

        st.text("--- НАЧАЛО ФАЙЛА ---")
        st.text(content)
        st.text("--- КОНЕЦ ---")
        st.info("Скопируйте этот текст и пришлите мне. Я увижу, как именно там записаны числа TEC.")

    except Exception as e:
        st.error(f"Ошибка: {e}")