"""Compare modes across key configs - single run."""
import sys, time
sys.path.insert(0, '.')
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

tests = [
    ("BTC/USDT", "Base",     0, 1, 1, 1, 0, 1, 1),
    ("BTC/USDT", "OTE_Only", 0, 0, 0, 1, 0, 1, 0),
    ("BTC/USDT", "KZ_ON",    1, 1, 1, 1, 0, 1, 1),
    ("ETH/USDT", "Base",     0, 1, 1, 1, 0, 1, 1),
    ("ETH/USDT", "OTE_Only", 0, 0, 0, 1, 0, 1, 0),
    ("ETH/USDT", "KOD_Only", 0, 0, 1, 0, 0, 1, 0),
    ("SOL/USDT", "Base",     0, 1, 1, 1, 0, 1, 1),
    ("SOL/USDT", "OTE_Only", 0, 0, 0, 1, 0, 1, 0),
    ("SOL/USDT", "M1_Only",  0, 1, 0, 0, 0, 1, 0),
    ("XAU/USD",  "M1_Only",  0, 1, 0, 0, 0, 1, 0),
]

print(f"{'Pair':<12} {'Config':<10} {'Mode':<13} {'Trades':<6} {'Win%':<6} {'PnL':<10} {'PF':<5} {'DD%':<6} {'Sharpe':<7} {'Time':<5}")
print("=" * 85)

for pair, label, kz, m1, kod, ote, bb, c3, mss in tests:
    clean = pair.replace("/", "_")
    df = ForexDataLoader().load_forex(clean, "4h")
    for mode in ['independent', 'tsq_trail']:
        t0 = time.time()
        bt = Backtester(initial_capital=10_000, risk_per_trade=0.02,
            use_kill_zone=kz, use_model1=m1, use_kod=kod, use_ote=ote,
            use_breaker_block=bb, use_candle3_only=c3, use_true_mss=mss,
            stop_mode=mode)
        res = bt.run(df, pair, stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0])
        t1 = time.time()
        print(f"{pair:<12} {label:<10} {mode:<13} {res['total_trades']:<6} {res['win_rate']:<6.1f} ${res['total_pnl']:<8.0f} {res['profit_factor']:<5.2f} {res['max_drawdown']:<6.1f} {res['sharpe_ratio']:<7.2f} {t1-t0:<5.0f}s")
        sys.stdout.flush()
