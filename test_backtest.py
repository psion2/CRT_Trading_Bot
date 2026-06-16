"""Quick performance test for CRT backtest."""
import time
import sys
sys.path.insert(0, 'E:\\MyWebProject\\CRT_Trading_Bot\\CRT_Trading_Bot')

from data.forex_loader import ForexDataLoader
from strategies.crt_strategy import CRTStrategyImpl
from backtest.backtester import Backtester

loader = ForexDataLoader()
df = loader.load_forex('EUR_USD')
print(f'Total candles: {len(df)}')

# Test performance with increasing sizes
for n in [100, 300, 500, 1000]:
    df_small = df.iloc[-n:].copy()
    t0 = time.time()
    strat = CRTStrategyImpl()
    result = strat.generate_signals(df_small)
    t1 = time.time()
    signals = (result["signal"] != 0).sum()
    print(f'n={n}: {t1-t0:.2f}s ({n/(t1-t0):.0f} c/s), signals={signals}')

# Run full backtest for first 1000 candles
print('\nRunning full backtest on 1000 candles...')
bt = Backtester(
    initial_capital=10_000,
    risk_per_trade=0.02,
    use_candle3_only=True,
    use_true_mss=True,
)
t0 = time.time()
results = bt.run(df.iloc[-1000:].copy(), 'EUR/USD', stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0])
t1 = time.time()
bt.print_results('EUR/USD')
print(f'Backtest took {t1-t0:.2f}s')
