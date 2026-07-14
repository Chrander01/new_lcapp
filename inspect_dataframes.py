from io import StringIO

import pandas as pd
import requests

DATASETS = {
    "c": "https://raw.githubusercontent.com/Chrander01/csv/main/FF_Daily.csv",
    "temp": "https://raw.githubusercontent.com/Chrander01/csv/main/temp.csv",
    "efport": "https://raw.githubusercontent.com/Chrander01/csv/main/efport.csv",
    "df_combined": "https://raw.githubusercontent.com/Chrander01/csv/main/df_combined.csv",
    "df_combined_10": "https://raw.githubusercontent.com/Chrander01/csv/main/df_combined_10.csv",
    "bins_df": "https://raw.githubusercontent.com/Chrander01/csv/main/bins_df.csv",
}

for name, url in DATASETS.items():
    df = pd.read_csv(StringIO(requests.get(url).text))
    print(f"\n=== {name} ({df.shape[0]} rows x {df.shape[1]} cols) ===")
    print(df)
