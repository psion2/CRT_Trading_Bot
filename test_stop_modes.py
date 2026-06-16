"""Test both stop modes on BTC/USDT."""
import sys, time
sys.path.insert(0, '.')
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

df = ForexDataLoader().load_forex('BTC_USDT', '4h')
print(f'Data: {len(df)} candles')

for mode in ['independent', 'tsq_trail']:
    t0 = time.time()
    bt = Backtester(initial_capital=10_000, risk_per_trade=0.02, stop_mode=mode)
    res = bt.run(df, 'BTC/USDT', stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0])
    t1 = time.time()
    print(f'{mode:<15} tr={res["total_trades"]:<4} wr={res["win_rate"]:<5.1f}% '
          f'pnl=${res["total_pnl"]:<8.2f} pf={res["profit_factor"]:<5.2f} '
          f'dd={res["max_drawdown"]:<5.1f}% ({t1-t0:.0f}s)')
