"""Compare old (4H close entry) vs new (signal level entry) on real data."""
import sys, time
from pathlib import Path

SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))

from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester
import pandas as pd
import numpy as np

loader = ForexDataLoader()

# Test with EUR/USD (fast, ~3100 4H candles)
pair, tf = "EUR_USD", "4h"
df = loader.load_forex(pair, tf)
if df.index.tz is not None:
    df.index = df.index.tz_localize(None)

print(f"Loaded {len(df)} candles for {pair} {tf}")

# Run with NEW entry logic (signal level entry, fixed % SL)
bt_new = Backtester(initial_capital=10_000, risk_per_trade=0.02, stop_mode="tsq_trail")
t0 = time.time()
r_new = bt_new.run(df.copy(), "EUR/USD", stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0])
t_new = time.time() - t0

print(f"\n{'='*60}")
print(f"NEW: Entry at signal level, SL fixed % from entry")
print(f"{'='*60}")
print(f"Trades: {r_new['total_trades']}, Win%: {r_new['win_rate']:.1f}%")
print(f"PnL: ${r_new['total_pnl']:.2f}, PF: {r_new['profit_factor']:.2f}")
print(f"DD: {r_new['max_drawdown']:.1f}%, Sharpe: {r_new['sharpe_ratio']:.2f}")
print(f"Time: {t_new:.1f}s")

# Show entry price distribution
entries = [t['entry_price'] for t in bt_new.trades]
closes = [t['entry_price'] for t in bt_new.trades]  # placeholder
print(f"\nEntry price stats: min={min(entries):.2f}, max={max(entries):.2f}, avg={np.mean(entries):.2f}")

# Count by phase type
from collections import Counter
phases = Counter(t['phase'] for t in bt_new.trades)
print("\nPhase distribution:")
for phase, count in phases.most_common():
    pnl_phase = sum(t['pnl'] for t in bt_new.trades if t['phase'] == phase)
    print(f"  {phase:12s}: {count:3d} trades, PnL=${pnl_phase:+.2f}")

# Show first/last trades
print(f"\nFirst 3 trades:")
for t in bt_new.trades[:3]:
    print(f"  {t['phase']:12s} {t['direction']:5s} entry=${t['entry_price']:.2f} sl=${t['stop_loss']:.2f} pnl=${t['pnl']:+.2f}")

print(f"\nLast 3 trades:")
for t in bt_new.trades[-3:]:
    print(f"  {t['phase']:12s} {t['direction']:5s} entry=${t['entry_price']:.2f} sl=${t['stop_loss']:.2f} pnl=${t['pnl']:+.2f}")
