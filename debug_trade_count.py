"""Debug: why trade count differs between scripts."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

loader = ForexDataLoader()
df = loader.load_forex("BTC_USDT", "4h")
if df.index.tz is not None:
    df.index = df.index.tz_localize(None)
print(f"Candles: {len(df)}")
print(f"Index tz: {df.index.tz}")

bt = Backtester(10000, 0.02,
    use_kill_zone=False, use_model1=True, use_kod=True, use_ote=True,
    use_breaker_block=True, use_candle3_only=True, use_true_mss=True,
    stop_mode="tsq_trail")

r = bt.run(df, "BTC/USDT", 0.015, [1.5, 2.0])
print(f"Trades: {r['total_trades']}, PnL: ${r['total_pnl']:.2f}")
print(f"Strategy params: {bt.strategy.params}")
