import streamlit as st
import earthaccess
import georinex as gr
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import gzip
import shutil

# ... (инициализация авторизации) ...

if st.button("🚀 Анализировать актуальные данные"):
    with st.spinner("Распаковка и чтение данных..."):
        try:
            results = earthaccess.search_data(
                short_name='GNSS_IGS_AC_ion_VTEC_comp',
                count=1
            )

            files = earthaccess.download(results, "data")
            raw_path = str(files[0])
            unpacked_path = raw_path + ".uncompressed"

            # Распаковка GZIP
            with gzip.open(raw_path, 'rb') as f_in:
                with open(unpacked_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Чтение
            # Попробуем использовать xarray напрямую, так как GIM файлы
            # часто являются netCDF, упакованными в IONEX-подобные имена
            try:
                ds = gr.load(unpacked_path)
            except:
                import xarray as xr

                # Многие файлы GIM от IGS на самом деле являются NetCDF
                ds = xr.open_dataset(unpacked_path)

            st.success("Данные успешно считаны!")

            # Визуализация
            fig, ax = plt.subplots(figsize=(10, 6))
            if 'TEC' in ds:
                ds['TEC'].isel(time=0).plot(ax=ax)
            else:
                st.write("Структура данных:", ds)
            st.pyplot(fig)

        except Exception as e:
            st.error(f"Ошибка: {e}")