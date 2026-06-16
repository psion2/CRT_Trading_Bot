"""Single BTC/USDT backtest."""
import time, sys
sys.path.insert(0, '.')
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

df = ForexDataLoader().load_forex('BTC_USDT', '4h')
print(f'Data loaded: {len(df)} candles')

bt = Backtester(initial_capital=10_000, risk_per_trade=0.02,
    use_candle3_only=True, use_true_mss=True)

for label, kz, m1, kod, ote, bb, c3, mss in [
    ("Base",     False, True,  True,  True, True,  True, True),
    ("KZ_ON",    True,  True,  True,  True, True,  True, True),
    ("C3_OFF",   False, True,  True,  True, True,  False,True),
    ("M1_Only",  False, True,  False, False,False, True, False),
    ("KOD_Only", False, False, True,  False,False, True, False),
    ("OTE_Only", False, False, False, True, False, True, False),
]:
    t0 = time.time()
    bt2 = Backtester(initial_capital=10_000, risk_per_trade=0.02,
        use_kill_zone=kz, use_model1=m1, use_kod=kod, use_ote=ote,
        use_breaker_block=bb, use_candle3_only=c3, use_true_mss=mss)
    res = bt2.run(df, 'BTC/USDT', stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0])
    t1 = time.time()
    print(f'{label:<10} tr={res["total_trades"]:<4} wr={res["win_rate"]:<5.1f}% '
          f'pnl=${res["total_pnl"]:<8.2f} pf={res["profit_factor"]:<5.2f} '
          f'dd={res["max_drawdown"]:<5.1f}% sharpe={res["sharpe_ratio"]:<7.2f} '
          f'({t1-t0:.0f}s)')
