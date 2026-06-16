"""Quick BTC + SOL comparison."""
import sys, time
sys.path.insert(0, '.')
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

for pair in ['BTC/USDT', 'SOL/USDT']:
    clean = pair.replace('/', '_')
    df = ForexDataLoader().load_forex(clean, '4h')
    for label, kz, m1, kod, ote, bb, c3, mss in [
        ('Base', 0, 1, 1, 1, 0, 1, 1),
        ('OTE_Only', 0, 0, 0, 1, 0, 1, 0),
    ]:
        parts = [f'{pair:<12} {label:<10}']
        for mode in ['independent', 'tsq_trail']:
            t0 = time.time()
            bt = Backtester(initial_capital=10_000, risk_per_trade=0.02,
                use_kill_zone=kz, use_model1=m1, use_kod=kod, use_ote=ote,
                use_breaker_block=bb, use_candle3_only=c3, use_true_mss=mss,
                stop_mode=mode)
            res = bt.run(df, pair, stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0])
            t1 = time.time()
            parts.append(f'{mode:<13} tr={res["total_trades"]:<5} wr={res["win_rate"]:<5.1f}% pnl=${res["total_pnl"]:<9.0f} dd={res["max_drawdown"]:<5.1f}% ({t1-t0:.0f}s)')
        print(' | '.join(parts))
