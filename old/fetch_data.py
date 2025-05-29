import requests
import pandas as pd
import os
from datetime import datetime

def fetch_btc_ohlc(days=1):
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc"
    params = {"vs_currency": "eur", "days": days}
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

def archive_btc_data(days=1, data_dir="data"):
    os.makedirs(data_dir, exist_ok=True)

    today_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{data_dir}/btc_ohlc_{today_str}.csv"

    if os.path.exists(filename):
        print(f"✅ Plik '{filename}' już istnieje – pomijam pobieranie.")
        return filename

    print(f"⬇️  Pobieranie danych za ostatnie {days} dni...")
    df = fetch_btc_ohlc(days=days)
    df.to_csv(filename, index=False)
    print(f"✅ Zapisano dane do: {filename}")
    return filename

if __name__ == "__main__":
    archive_btc_data(days=1)
