# CRT Trading Bot - Configuration

# Trading Pairs
PAIRS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "GBP/USD",
]

# Timeframe
TIMEFRAME = "4h"

# Capital
INITIAL_CAPITAL = 10_000

# Risk Management
RISK_PER_TRADE = 0.03  # 3%
STOP_LOSS_PCT = 0.02   # 2%
TAKE_PROFITS = [1.5, 2.0]  # R:R ratios

# Backtesting
START_DATE = "2025-05-01"
END_DATE = "2026-05-10"