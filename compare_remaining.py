"""Remaining tests: SOL tsq_trail, XAU."""
import sys, time
sys.path.insert(0, '.')
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

tests = [
    ("SOL/USDT", "Base",     0, 1, 1, 1, 0, 1, 1, 'tsq_trail'),
    ("SOL/USDT", "OTE_Only", 0, 0, 0, 1, 0, 1, 0, 'tsq_trail'),
    ("SOL/USDT", "M1_Only",  0, 1, 0, 0, 0, 1, 0, 'independent'),
    ("SOL/USDT", "M1_Only",  0, 1, 0, 0, 0, 1, 0, 'tsq_trail'),
    ("XAU/USD",  "M1_Only",  0, 1, 0, 0, 0, 1, 0, 'independent'),
    ("XAU/USD",  "M1_Only",  0, 1, 0, 0, 0, 1, 0, 'tsq_trail'),
]

for pair, label, kz, m1, kod, ote, bb, c3, mss, mode in tests:
    clean = pair.replace("/", "_")
    df = ForexDataLoader().load_forex(clean, "4h")
    t0 = time.time()
    bt = Backtester(initial_capital=10_000, risk_per_trade=0.02,
        use_kill_zone=kz, use_model1=m1, use_kod=kod, use_ote=ote,
        use_breaker_block=bb, use_candle3_only=c3, use_true_mss=mss,
        stop_mode=mode)
    res = bt.run(df, pair, stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0])
    t1 = time.time()
    print(f"{pair:<12} {label:<10} {mode:<13} tr={res['total_trades']:<5} wr={res['win_rate']:<5.1f}% pnl=${res['total_pnl']:<8.0f} pf={res['profit_factor']:<5.2f} dd={res['max_drawdown']:<5.1f}% sharpe={res['sharpe_ratio']:<6.2f} ({t1-t0:.0f}s)")
    sys.stdout.flush()
