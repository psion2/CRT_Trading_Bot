"""Full comparison: independent vs tsq_trail across all pairs."""
import sys, time
sys.path.insert(0, '.')
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "EUR/USD", "GBP/USD", "XAU/USD"]
CONFIGS = [
    ("Base",     False, True,  True,  True,  False, True, True),
    ("KZ_ON",    True,  True,  True,  True,  False, True, True),
    ("OTE_Only", False, False, False, True,  False, True, False),
    ("M1_Only",  False, True,  False, False, False, True, False),
    ("KOD_Only", False, False, True,  False, False, True, False),
]

print(f"{'Pair':<12} {'Config':<10} {'Mode':<13} {'Trades':<7} {'Win%':<7} {'PnL':<12} {'PF':<6} {'DD%':<7} {'Time':<6}")
print("=" * 85)

for pair_name in PAIRS:
    clean = pair_name.replace("/", "_")
    df = ForexDataLoader().load_forex(clean, "4h")

    for label, kz, m1, kod, ote, bb, c3, mss in CONFIGS:
        for mode in ['independent', 'tsq_trail']:
            t0 = time.time()
            bt = Backtester(initial_capital=10_000, risk_per_trade=0.02,
                use_kill_zone=kz, use_model1=m1, use_kod=kod, use_ote=ote,
                use_breaker_block=bb, use_candle3_only=c3, use_true_mss=mss,
                stop_mode=mode)
            res = bt.run(df, pair_name, stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0])
            t1 = time.time()
            print(f"{pair_name:<12} {label:<10} {mode:<13} {res['total_trades']:<7} {res['win_rate']:<7.1f} ${res['total_pnl']:<9.2f} {res['profit_factor']:<6.2f} {res['max_drawdown']:<6.1f}% {t1-t0:<5.0f}s")
