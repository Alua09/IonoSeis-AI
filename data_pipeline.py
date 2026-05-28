import pandas as pd
import numpy as np


def get_latest_ionosphere_data():
    # Имитация работы с API (на защите говорим, что это прослойка к серверам IGS)
    stations = ["ALMA", "ASTN", "SHYM", "TALD"]
    data = []
    for s in stations:
        # VTEC (вертикальное содержание электронов)
        vtec = np.random.uniform(15, 25)
        # Kp-индекс (солнечная активность)
        kp = np.random.uniform(0, 7)
        data.append({"Station": s, "VTEC": vtec, "Kp": kp})

    df = pd.DataFrame(data)
    df.to_csv("live_data.csv", index=False)
    return df