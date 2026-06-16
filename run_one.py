"""Run one pair backtest, print CSV result."""
import sys, time, json
sys.path.insert(0, '.')
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

pair = sys.argv[1]
clean = pair.replace("/", "_")
df = ForexDataLoader().load_forex(clean, "4h")

for label, kz, m1, kod, ote, bb, c3, mss in [
    ("Base",     False, True,  True,  True, True,  True, True),
    ("KZ_ON",    True,  True,  True,  True, True,  True, True),
    ("OTE_Only", False, False, False, True, False, True, False),
    ("M1_Only",  False, True,  False, False,False, True, False),
    ("KOD_Only", False, False, True,  False,False, True, False),
]:
    t0 = time.time()
    bt = Backtester(initial_capital=10_000, risk_per_trade=0.02,
        use_kill_zone=kz, use_model1=m1, use_kod=kod, use_ote=ote,
        use_breaker_block=bb, use_candle3_only=c3, use_true_mss=mss)
    res = bt.run(df, pair, stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0])
    elapsed = time.time() - t0
    print(f"{pair},{label},{res['total_trades']},{res['win_rate']:.1f},{res['total_pnl']:.2f},{res['profit_factor']:.2f},{res['max_drawdown']:.1f},{res['sharpe_ratio']:.2f},{elapsed:.0f}")
