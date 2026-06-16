"""Quick test of corrected limit_retest logic."""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

loader = ForexDataLoader()
df = loader.load_forex("BTC_USDT", "4h")
df15 = loader.load_forex("BTC_USDT", "15m")
if df.index.tz is not None: df.index = df.index.tz_localize(None)
if df15.index.tz is not None: df15.index = df15.index.tz_localize(None)

for mode, logic, rw in [
    ("immediate", None, 0),
    ("limit_retest", "extreme", 0),
    ("limit_retest", "extreme", 8),
    ("ltf", None, 0),
]:
    kwargs = dict(initial_capital=10000, risk_per_trade=0.02,
                  stop_mode="tsq_trail", max_leverage=3,
                  entry_mode=mode, retest_window=rw)
    if logic: kwargs["entry_logic"] = logic
    bt = Backtester(**kwargs)
    r = bt.run(df.copy(), "BTC/USDT", 0.015, [1.5, 2.0], ltf_df=df15)
    t = r["trade_log"]
    ph = t["phase"].value_counts().to_dict()
    print(f"{mode:20s} rw={rw}  tr={r['total_trades']:4d}  pnl=${r['total_pnl']:>8,.2f}  "
          f"win={r['win_rate']:.1f}%  dd={r['max_drawdown']:.1f}%  "
          f"sh={r['sharpe_ratio']:.2f}  miss={r.get('missed_orders',0)}")
    print(f"  Phases: {ph}")
