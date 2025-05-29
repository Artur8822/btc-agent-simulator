"""
agent.py

Contains agent classes responsible for decision-making:

1. ExecutorAgent - Executes BTC/EUR investment actions.
   - Takes into account transaction fees.
   - Makes buy/sell decisions based on advisor recommendations and net profit expectations.
   - Logs every action (including passive observations) to a persistent action log.

2. AdvisorAgent - Serves as a market trend advisor.
   - Analyzes the MA5 vs MA20 trend.
   - Recommends: 'buy', 'sell', or 'hold' based on recent moving average patterns.

This module is part of a scientific simulation designed to test agent behavior and market strategies.
"""



import csv
import os
import pandas as pd

# exeadvisor_agentutor_agent

class AdvisorAgent:
    def __init__(self, trend_confirmations=3):
        self.trend_confirmations = trend_confirmations

    def advise(self, price_history_df):
        if len(price_history_df) < 20:
            return "hold", "Zbyt mało danych do oceny."

        df = price_history_df.copy()
        df["MA5"] = df["close"].rolling(window=5).mean()
        df["MA20"] = df["close"].rolling(window=20).mean()

        recent = df.tail(self.trend_confirmations)
        trend_up = all(recent["MA5"] > recent["MA20"])
        trend_down = all(recent["MA5"] < recent["MA20"])

        if trend_up:
            return "buy", "Trend wzrostowy potwierdzony przez ostatnie {} pomiarów.".format(self.trend_confirmations)
        elif trend_down:
            return "sell", "Trend spadkowy potwierdzony przez ostatnie {} pomiarów.".format(self.trend_confirmations)
        else:
            return "hold", "Brak wyraźnego trendu w MA5 vs MA20."


# executor_agent

class ExecutorAgent:
    def __init__(self, capital=1000.0, fee_rate=0.002, min_expected_profit=1.0):
        self.initial_capital = capital
        self.capital = capital
        self.position = 0
        self.entry_price = 0
        self.fee_rate = fee_rate
        self.min_expected_profit = min_expected_profit
        self.actions_log_path = "logs/actions_log.csv"
        os.makedirs("logs", exist_ok=True)

        if not os.path.exists(self.actions_log_path):
            with open(self.actions_log_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "executor_action", "advisor_suggestion", "comment", "price", "fee", "btc", "capital", "net_profit"])

    def log_action(self, timestamp, action, suggestion, comment, price, fee, btc_amount, profit=0.0):
        with open(self.actions_log_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, action, suggestion, comment,
                round(price, 2), round(fee, 2), round(btc_amount, 6), round(self.capital, 2), round(profit, 2)
            ])

    def _estimate_fees(self, amount):
        return amount * self.fee_rate

    def estimate_net_profit(self, current_price):
        if self.position == 0:
            return 0
        gross = self.position * current_price
        fee_exit = self._estimate_fees(gross)
        fee_entry = self._estimate_fees(self.entry_price * self.position)
        net = gross - fee_exit - fee_entry
        return net - self.initial_capital

    def buy(self, price, timestamp, suggestion, comment):
        fee = self._estimate_fees(self.capital)
        investable = self.capital - fee
        btc = investable / price
        self.position = btc
        self.entry_price = price
        self.capital = 0
        print(f"Executor: Zdecydowano KUPNO @ {price:.2f} EUR | Sugerowane: {suggestion} | Komentarz: {comment}")
        self.log_action(timestamp, "BUY", suggestion, comment, price, fee, btc)

    def sell(self, price, timestamp, suggestion, comment):
        gross = self.position * price
        fee = self._estimate_fees(gross)
        net = gross - fee
        profit = net - self.initial_capital
        self.capital = net
        print(f"Executor: SPRZEDAŻ @ {price:.2f} EUR | Zysk: {profit:.2f} | Sugerowane: {suggestion} | Komentarz: {comment}")
        self.log_action(timestamp, "SELL", suggestion, comment, price, fee, self.position, profit)
        self.position = 0
        self.entry_price = 0

    def decide(self, price, timestamp, suggestion, comment):
        if self.capital > 0 and self.position == 0 and suggestion == "buy":
            self.buy(price, timestamp, suggestion, comment)
        elif self.position > 0:
            expected = self.estimate_net_profit(price)
            if suggestion == "sell" or expected >= self.min_expected_profit:
                self.sell(price, timestamp, suggestion, comment)