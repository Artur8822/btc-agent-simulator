import pandas as pd
import os
import time
from datetime import datetime

def summarize_logs(log_path="logs/actions_log.csv", summary_dir="summary"):
    if not os.path.exists(log_path):
        print("Brak pliku z logami agenta.")
        return

    os.makedirs(summary_dir, exist_ok=True)

    df = pd.read_csv(log_path)

    total_fee = df["fee"].sum()
    total_profit = df["net_profit"].sum()
    total_trades = len(df)
    buys = len(df[df["executor_action"] == "BUY"])
    sells = len(df[df["executor_action"] == "SELL"])
    capital = df["capital"].iloc[-1] if not df.empty else 0

    now = datetime.now()
    filename = f"{summary_dir}/summary_{now.strftime('%Y-%m-%d_%H')}.csv"

    summary = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "trades_total": total_trades,
        "buys": buys,
        "sells": sells,
        "total_fee": round(total_fee, 2),
        "total_profit": round(total_profit, 2),
        "final_capital": round(capital, 2)
    }

    pd.DataFrame([summary]).to_csv(filename, index=False)
    print(f"✅ Zapisano podsumowanie do: {filename}")


def main():
    print("📊 Analiza cykliczna co godzinę – rozpoczęta.")
    while True:
        summarize_logs()
        time.sleep(3600)  # 3600 sekund = 1 godzina


if __name__ == "__main__":
    main()
