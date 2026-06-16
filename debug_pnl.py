"""Debug the massive PnL spike."""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

loader = ForexDataLoader()
df = loader.load_forex("BTC_USDT", "4h")
if df.index.tz is not None:
    df.index = df.index.tz_localize(None)

bt = Backtester(10000, 0.02,
    use_model1=True, use_kod=True, use_ote=True, use_breaker_block=True,
    use_candle3_only=True, use_true_mss=True,
    stop_mode="tsq_trail")
r = bt.run(df, "BTC/USDT", 0.015, [1.5, 2.0])

# Find the wildest trades
trades = r["trade_log"]
if len(trades) > 0:
    trades["abs_pnl"] = trades["pnl"].abs()
    top = trades.nlargest(10, "abs_pnl")
    for _, t in top.iterrows():
        print(f"PnL=${t['pnl']:<+10.2f}  size={t['position_size']:<10.2f}  risk={t['original_risk']:<10.6f}  entry={t['entry_price']:<10.4f}  sl={t['stop_loss']:<10.4f}  phase={t['phase']:<10}  reason={t['exit_reason']:<10}")

    print(f"\nTotal trades: {len(trades)}")
    print(f"Total PnL: ${r['total_pnl']:.2f}")
    print(f"Win rate: {r['win_rate']:.1f}%")

    # Check if risk is ever zero or tiny
    tiny = trades[trades["original_risk"] < 0.0001]
    print(f"\nTrades with risk < 0.0001: {len(tiny)}")
    if len(tiny) > 0:
        for _, t in tiny.iterrows():
            print(f"  risk={t['original_risk']:.10f}  entry={t['entry_price']}  sl={t['stop_loss']}  pnl=${t['pnl']:.2f}")
