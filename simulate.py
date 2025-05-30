"""
simulate.py

Main loop for real-time market simulation.

Every minute:
- Fetches current BTC/EUR price from CoinGecko.
- Saves the price to an hourly CSV file (acts as historical price database).
- Invokes AdvisorAgent to generate a market recommendation.
- Allows ExecutorAgent to act on the recommendation (or not).
- Logs all actions (even 'NONE') into a daily CSV action log.
- Generates hourly summaries of trading performance.

This script is intended to run continuously and accumulate historical market data
for analysis and future model development.

Author: Artur
"""


# simulate_live.py
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import csv
from agent import AdvisorAgent
from agent import ExecutorAgent


def get_live_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "eur"}
    try:
        response = requests.get(url, params=params)
        return response.json()["bitcoin"]["eur"]
    except:
        return None


def log_price_to_file(timestamp, price, data_dir="data"):
    os.makedirs(data_dir, exist_ok=True)
    hour_str = timestamp.strftime("%Y-%m-%d_%H")
    filepath = os.path.join(data_dir, f"btc_prices_{hour_str}.csv")

    file_exists = os.path.isfile(filepath)
    with open(filepath, mode="a", newline="") as f:  # <-- APPEND mode
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "price"])
        writer.writerow([timestamp.strftime("%Y-%m-%d %H:%M:%S"), round(price, 2) if price is not None else "NaN"])

    print(f" Price is saved: {price} under {filepath}")



def summarize_logs(log_path="logs/actions_log.csv", summary_dir="summary"):
    if not os.path.exists(log_path):
        print("Missing log file with agents actions.")
        return

    os.makedirs(summary_dir, exist_ok=True)

    df = pd.read_csv("logs/actions_log_2025-05-30.csv", encoding="utf-8-sig")


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
    print(f"Summary is saved under: {filename}")


def log_minute_action(timestamp, action, suggestion, comment, price, fee, btc_amount, capital, profit, executor_thoughts, advisor_thoughts):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    date_str = timestamp.strftime("%Y-%m-%d")
    filepath = os.path.join(log_dir, f"actions_log_{date_str}.csv")

    file_exists = os.path.isfile(filepath)
    with open(filepath, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "executor_action", "advisor_suggestion", "comment", "price", "fee", "btc", "capital", "net_profit", "executor_thoughts", "advisor_thoughts"])
        writer.writerow([
            timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            action, suggestion, comment,
            round(price, 2), round(fee, 2), round(btc_amount, 6), round(capital, 2), round(profit, 2),
            executor_thoughts, advisor_thoughts
        ])


last_logged_hour = None

def main():
    advisor = AdvisorAgent(trend_confirmations=3)
    executor = ExecutorAgent(capital=1000.0)
    price_history = []
    start_time = datetime.now()

    print("Simulation LIVE just started...")
    while True:
        price = get_live_price()
        now = datetime.now()

        log_price_to_file(now, price)

        if price is not None:
            elapsed = now - start_time
            elapsed_str = str(timedelta(seconds=elapsed.total_seconds())).split('.')[0]
            print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Cena BTC: {price:.2f} EUR | Czas symulacji: {elapsed_str}")

            price_history.append({"timestamp": now, "close": price})
            df = pd.DataFrame(price_history)

            suggestion, comment = advisor.advise(df)
            previous_position = executor.position
            previous_capital = executor.capital

            executor_thoughts = f"Monitoring position. Capital: {executor.capital:.2f} EUR"
            advisor_thoughts = f"Advisor suggests: {suggestion.upper()} based on trend"

            executor.decide(price, now.strftime("%Y-%m-%d %H:%M:%S"), suggestion, comment)

            if executor.position == previous_position and executor.capital == previous_capital:
                log_minute_action(
                    now, "NONE", suggestion, "No action - more observations needed",
                    price, 0.0, executor.position, executor.capital, executor.estimate_net_profit(price),
                    executor_thoughts, advisor_thoughts
                )

            global last_logged_hour
            current_hour = now.replace(minute=0, second=0, microsecond=0)
            if last_logged_hour != current_hour:
                summarize_logs()
                last_logged_hour = current_hour

        time.sleep(60)


if __name__ == "__main__":
    main()
