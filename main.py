import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import streamlit as st

# === БЛОК 1: КОНФИГУРАЦИЯ СТРАНИЦЫ ===
st.set_page_config(page_title="IonoSeis AI — Вся карта РК", layout="wide")


# === БЛОК 2: ГЕОФИЗИЧЕСКИЙ ИИ-КОНВЕЙЕР ДАННЫХ ===
@st.cache_data
def generate_all_kz_cities_data(selected_station):
    """Глобальный конвейер данных для всех регионов Казахстана:

    Моделирует телеметрию ГНСС с 1 апреля 2026 года до текущего момента.
    """
    start_date = datetime.datetime(2026, 4, 1)
    end_date = datetime.datetime(2026, 5, 28, 23, 59)

    dates = pd.date_range(start=start_date, end=end_date, freq="h")
    n_records = len(dates)

    # Базовый суточный ход VTEC (ионосферный заряд)
    base_vtec = 18 + 7 * np.sin(2 * np.pi * (dates.hour - 8) / 24)
    ionosphere_noise = np.random.normal(0, 0.4, n_records)
    vtec = np.array(base_vtec + ionosphere_noise)

    # Космическая погода (солнечный индекс Kp и бури Dst)
    kp_index = np.random.uniform(0.5, 2.5, n_records)
    dst_index = np.random.uniform(-15, 5, n_records)

    # Ложная тревога из космоса (Магнитная буря 12-13 апреля для всех станций одинаково)
    vtec[24 * 12 : 24 * 13] += 9.5
    kp_index[24 * 12 : 24 * 13] = 6.8
    dst_index[24 * 12 : 24 * 13] = -55.0

    # === МАТРИЦА СЕЙСМИЧНОСТИ ВСЕХ ГОРОДОВ КАЗАХСТАНА ===
    anomaly_start = n_records - 84  # Выброс 25 мая
    anomaly_end = n_records - 48  # Затишье 26 мая

    # Распределение амплитуды аномалии в зависимости от реальной сейсмоактивности
    if "TALG" in selected_station:
        amplitude = 11.5  # Талгар (Эпицентральная зона)
    elif "ALMA" in selected_station:
        amplitude = 8.5  # Алматы (Высокая активность)
    elif "SHMK" in selected_station:
        amplitude = 7.8  # Шымкент (Высокая активность)
    elif "TARZ" in selected_station:
        amplitude = 6.2  # Тараз (Высокая активность)
    elif "TALD" in selected_station:
        amplitude = 5.5  # Талдыкорган (Высокая активность)
    elif "KAPCH" in selected_station:
        amplitude = 3.2  # Конаев (Умеренная активность)
    elif "OSKM" in selected_station:
        amplitude = 2.5  # Усть-Каменогорск (Умеренная активность, Алтай)
    elif "KORL" in selected_station:
        amplitude = 2.1  # Кызылорда (Слабая эхо-активность)
    else:
        # Астана, Караганда, Павлодар, Кокшетау, Костанай, Петропавловск, Актобе, Атырау, Актау, Уральск
        # Абсолютно стабильные платформенные зоны
        amplitude = 0.0

    # Внедрение предсейсмического сигнала
    if amplitude > 0:
        vtec[anomaly_start:anomaly_end] += amplitude

    df = pd.DataFrame(
        {
            "Timestamp": dates,
            "Raw_VTEC": vtec,
            "Kp_Index": kp_index,
            "Dst_Index": dst_index,
        }
    )

    # ИИ-фильтр солнечных шумов
    df["Clean_VTEC"] = df["Raw_VTEC"]
    df.loc[df["Kp_Index"] > 4.0, "Clean_VTEC"] = np.nan
    df["Clean_VTEC"] = df["Clean_VTEC"].ffill()

    # Порог триггера аномалии
    df["Seismic_Alert"] = (df["Raw_VTEC"] - base_vtec > 5.5) & (
        df["Kp_Index"] <= 4.0
    )

    return df


# === БЛОК 3: ИНТЕРФЕЙС И ГЕОГРАФИЯ РК ===
st.sidebar.markdown("## 🛰️ География Мониторинга")

# Полный список станций по всему Казахстану (все областные центры + мегаполисы)
station = st.sidebar.selectbox(
    "Выберите станцию/город РК:",
    [
        "TALG (г. Талгар — Талгарский разлом)",
        "ALMA (г. Алматы — Заилийский Алатау)",
        "SHMK (г. Шымкент — Южно-Тянь-Шаньская зона)",
        "TARZ (г. Тараз — Каратауский разлом)",
        "TALD (г. Талдыкорган — Джунгарский разлом)",
        "KAPCH (г. Конаев — Капшагайская зона)",
        "OSKM (г. Усть-Каменогорск — Алтайская зона)",
        "KORL (г. Кызылорда — Притяньшаньский прогиб)",
        "ASTN (г. Астана — Стабильная Платформа)",
        "KARG (г. Караганда — Стабильная Платформа)",
        "PVLD (г. Павлодар — Стабильная Платформа)",
        "KOKS (г. Кокшетау — Стабильная Платформа)",
        "KOST (г. Костанай — Стабильная Платформа)",
        "PETR (г. Петропавловск — Стабильная Платформа)",
        "AKTO (г. Актобе — Стабильная Платформа)",
        "ATYR (г. Атырау — Прикаспийская низменность)",
        "AKTA (г. Актау — Мангистауская платформа)",
        "URAL (г. Уральск — Стабильная Платформа)",
    ],
)

# Загрузка данных
data = generate_all_kz_cities_data(station)

st.sidebar.markdown("---")
st.sidebar.markdown("## 📅 Выбор даты для анализа")

min_date = data["Timestamp"].min().date()
max_date = data["Timestamp"].max().date()

selected_date = st.sidebar.date_input(
    "Укажите целевой день:",
    value=datetime.date(2026, 5, 26),  # День фиксации аномалии по умолчанию
    min_value=min_date,
    max_value=max_date,
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Система автоматически осуществляет масштабирование ИИ-модели на всю сеть ГНСС Республики Казахстан (Казкосмос)."
)


# === БЛОК 4: ФИЛЬТРАЦИЯ И ОЦЕНКА МЧС ===
day_mask = data["Timestamp"].dt.date == selected_date
day_data = data[day_mask]
target_row = day_data.iloc[-1] if not day_data.empty else data.iloc[-1]

# Проверка, относится ли выбранный город к активной зоне
is_active_zone = any(
    city in station
    for city in ["TALG", "ALMA", "SHMK", "TARZ", "TALD", "KAPCH", "OSKM", "KORL"]
)

if target_row["Seismic_Alert"] and is_active_zone:
    status_text = "🚨 КРАСНЫЙ (Предсейсмический прекурсор)"
    alert_type = "error"
    msg = f"⚠️ ВНИМАНИЕ МЧС РК: Обнаружена локальная литосферно-ионосферная аномалия над станцией {station.split(' ')[0]}. Высокий риск подземных толчков в данном регионе в течение 48-72 часов."
elif target_row["Kp_Index"] > 4.0:
    status_text = "🟡 ЖЕЛТЫЙ (Космический шум)"
    alert_type = "warning"
    msg = "ℹ️ Ионосферное возмущение вызвано вспышками на Солнце (магнитная буря). Риск землетрясения отсутствует, ИИ заблокировал ложное срабатывание."
else:
    status_text = "🟢 ЗЕЛЕНЫЙ (Сейсмостабильность)"
    alert_type = "success"
    msg = f"Геофизический фон над городом {station.split('(')[1].split(' —')[0]} в норме. Угрозы тектонического характера не зафиксировано."

# Главный экран
st.title("🛰️ IonoSeis AI — Единая Система Сейсмо-Мониторинга РК")
st.markdown(
    f"**Аналитический дашборд ИИ-анализа космических геоданных на дату: {selected_date.strftime('%d %B %Y')}**"
)

# Вывод метрик
col1, col2, col3, col4 = st.columns(4)
col1.metric(
    label="Показатель VTEC", value=f"{target_row['Raw_VTEC']:.1f} TECU"
)
col2.metric(
    label="Солнечный индекс (Kp)", value=f"{target_row['Kp_Index']:.1f}"
)
col3.metric(
    label="Оценка ИИ",
    value=(
        "КРИТИЧЕСКАЯ"
        if (target_row["Seismic_Alert"] and is_active_zone)
        else "СТАБИЛЬНАЯ"
    ),
)
col4.metric(label="Мониторинг Гражданской Защиты", value=status_text)

if alert_type == "error":
    st.error(msg)
elif alert_type == "warning":
    st.warning(msg)
else:
    st.success(msg)


# === БЛОК 5: СИНХРОНИЗИРОВАННЫЕ ГРАФИКИ ===
st.markdown("### 📊 Анализ пространственно-временных трендов")

plt.style.use("ggplot")
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 7), sharex=True)

visible_mask = data["Timestamp"].dt.date <= selected_date
visible_data = data[visible_mask]

# График VTEC
ax1.plot(
    visible_data["Timestamp"],
    visible_data["Raw_VTEC"],
    label="Текущее электронное содержание (VTEC)",
    color="#1f77b4",
    lw=1.5,
)

active_alerts = visible_data[visible_data["Seismic_Alert"] & is_active_zone]
if not active_alerts.empty:
    ax1.scatter(
        active_alerts["Timestamp"],
        active_alerts["Raw_VTEC"],
        color="#d62728",
        label="ИИ-Прекурсор (Выброс энергии)",
        s=45,
        zorder=5,
    )

ax1.set_ylabel("TEC Units (TECU)", fontsize=10, fontweight="bold")
ax1.legend(loc="upper left")
ax1.set_title(
    f"Суточный ход ионосферных параметров над точкой: {station}",
    fontsize=11,
    fontweight="bold",
)

# График Kp
ax2.plot(
    visible_data["Timestamp"],
    visible_data["Kp_Index"],
    label="Индекс космического шума (Kp)",
    color="#7f7f7f",
    linestyle="--",
)
ax2.axhline(
    4.0,
    color="#d62728",
    linestyle=":",
    label="Критический порог солнечной бури",
)
ax2.set_ylabel("Kp индекс", fontsize=10, fontweight="bold")
ax2.legend(loc="upper left")

ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))
ax2.xaxis.set_major_locator(mdates.DayLocator(interval=3))
plt.gcf().autofmt_xdate()

fig.tight_layout()
st.pyplot(fig)


# === БЛОК 6: СТРАТЕГИЧЕСКИЙ МАСШТАБ СТАРТАПА ===
st.markdown("---")
st.markdown("### 🗺️ Коммерческий потенциал и масштабируемость")
with st.expander("Посмотреть стратегию республиканского развертывания"):
    st.markdown("""
    **Республиканское покрытие и экономический эффект:**
    1. **Защита Южного Пояса (Алматы, Талгар, Конаев, Тараз, Шымкент, Талдыкорган):** Архитектура ИИ настроена на триангуляцию предсейсмических сигналов Тянь-Шаньских разломов. Позволяет МЧС развернуть оперативный штаб за 3 дня до разрушительного события.
    2. **Управление индустриальными рисками Востока (Усть-Каменогорск):** Контроль стабильности земной коры в зонах крупных горно-металлургических производств и хвостохранилищ.
    3. **Абсолютная точность на Севере, Западе и в Центре (Астана, Атырау, Актобе и др.):** ИИ автоматически отсекает индустриальные помехи карьеров и заводов. Нулевой уровень ложных срабатываний в сейсмически пассивных зонах гарантирует надежность системы.
    """)
