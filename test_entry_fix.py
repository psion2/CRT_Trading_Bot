"""Quick test for updated strategy entry logic."""
import sys
from pathlib import Path

SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))

from strategies.crt_strategy import CRTStrategyImpl
from backtest.backtester import Backtester
import pandas as pd
import numpy as np

dates = pd.date_range("2025-01-01", periods=500, freq="4h")
prices = [50000]
for i in range(499):
    prices.append(prices[-1] + np.random.randn() * 500 + (50 if i % 20 < 10 else -50))

df = pd.DataFrame({
    "open": prices, "high": [p + abs(np.random.randn() * 300) for p in prices],
    "low": [p - abs(np.random.randn() * 300) for p in prices],
    "close": [p + np.random.randn() * 200 for p in prices],
    "volume": np.random.randint(1000, 10000, 500),
}, index=dates)

bt = Backtester(initial_capital=10000, risk_per_trade=0.03)
r = bt.run(df, "TEST", stop_loss_pct=0.02, take_profit_ratios=[1.5, 2.0])
print(f"Trades: {r['total_trades']}, PnL: ${r['total_pnl']:.2f}, Sharpe: {r['sharpe_ratio']:.2f}, DD: {r['max_drawdown']:.1f}%")

print("\nSample trades:")
for t in bt.trades[:5]:
    print(f"  {t['phase']:12s} {t['direction']:5s} entry=${t['entry_price']:>8.2f} sl=${t['stop_loss']:>8.2f} risk=${t['original_risk']:>6.2f} pnl=${t['pnl']:>+8.2f} exit={t['exit_reason']}")

# Verify entry prices are signal levels, not 4H close
print("\nEntry price check (should NOT equal 4H close for all):")
signals = bt.strategy.generate_signals(df)
sig_rows = signals[signals["signal"] != 0]
for idx, row in sig_rows.head(5).iterrows():
    print(f"  {idx}: signal={row['signal']}, phase={row['crt_phase']}, entry={row['crt_inv_price']:.2f}, close={row['close']:.2f}, diff={row['close'] - row['crt_inv_price']:.2f}")
