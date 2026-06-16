"""Verify compliance fixes and compare modes."""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

loader = ForexDataLoader()
df = loader.load_forex("BTC_USDT", "4h")
if df.index.tz is not None:
    df.index = df.index.tz_localize(None)

# Mode A: CRT entry, no retest (retest_window=0)
bt_a = Backtester(10000, 0.02, stop_mode="tsq_trail", retest_window=0)
r_a = bt_a.run(df.copy(), "BTC/USDT", 0.015, [1.5, 2.0])

# Mode B: CRT entry, 4-candle retest wait (default)
bt_b = Backtester(10000, 0.02, stop_mode="tsq_trail", retest_window=4)
r_b = bt_b.run(df.copy(), "BTC/USDT", 0.015, [1.5, 2.0])

print(f"Mode A (no retest wait, CRT entry):")
print(f"  Trades={r_a['total_trades']}, PnL=${r_a['total_pnl']:.2f}, WR={r_a['win_rate']:.1f}%")

print(f"Mode B (4-candle retest wait, CRT entry):")
print(f"  Trades={r_b['total_trades']}, PnL=${r_b['total_pnl']:.2f}, WR={r_b['win_rate']:.1f}%")

# Check SL direction correctness
trades_b = r_b["trade_log"]
bad_sl = 0
for _, t in trades_b.iterrows():
    if t["direction"] == "long" and t["stop_loss"] >= t["entry_price"]:
        bad_sl += 1
    elif t["direction"] == "short" and t["stop_loss"] <= t["entry_price"]:
        bad_sl += 1

print(f"  Bad SL direction (SL on wrong side of entry): {bad_sl}")
print(f"  Min risk: ${trades_b['original_risk'].min():.6f}")
print(f"  Max risk: ${trades_b['original_risk'].max():.2f}")
print(f"  Median risk: ${trades_b['original_risk'].median():.2f}")

# Check if any trade has risk == 0 or negative
zero_risk = len(trades_b[trades_b["original_risk"] <= 0])
print(f"  Zero-risk trades: {zero_risk}")

# Sample a few trades to verify details
print("\nSample trades (3 winners, 3 losers):")
wins = trades_b[trades_b["pnl"] > 0].head(3)
losses = trades_b[trades_b["pnl"] <= 0].head(3)
for _, t in pd.concat([wins, losses]).iterrows():
    direction = t["direction"]
    entry = t["entry_price"]
    sl = t["stop_loss"]
    risk = t["original_risk"]
    sl_ok = "OK" if (direction == "long" and sl < entry) or (direction == "short" and sl > entry) else "WRONG"
    print(f"  {t['phase']:<8} {direction:<5} entry={entry:<10.2f} sl={sl:<10.2f} risk={risk:<10.2f} SL={sl_ok} PnL=${t['pnl']:<+.2f}")
