"""Optimized multi-asset backtest runner - precomputes shared data."""
import sys, time, gc
from pathlib import Path

SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))

from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester
from strategies.crt_strategy import CRTStrategyImpl
import pandas as pd
import numpy as np

loader = ForexDataLoader()

# Load all 4H data
ALL_PAIRS = {
    "BTC/USDT": loader.load_forex("BTC_USDT", "4h"),
    "ETH/USDT": loader.load_forex("ETH_USDT", "4h"),
    "EUR/USD": loader.load_forex("EUR_USD", "4h"),
    "XAU/USD": loader.load_forex("XAU_USD", "4h"),
    "SOL/USDT": loader.load_forex("SOL_USDT", "4h"),
    "GBP/USD": loader.load_forex("GBP_USD", "4h"),
}

# Load 15m LTF data for crypto
def load_ltf(name):
    try:
        return loader.load_forex(name, "15m")
    except:
        return None

LTF = {"BTC/USDT": load_ltf("BTC_USDT"), "ETH/USDT": load_ltf("ETH_USDT"), "SOL/USDT": load_ltf("SOL_USDT")}

# Configs to test
CONFIGS = [
    {"label": "Base", "use_kill_zone": False, "use_candle3_only": True, "use_true_mss": True,
     "use_model1": True, "use_ote": True, "use_kod": True, "use_breaker_block": True},
    {"label": "KZ_ON", "use_kill_zone": True, "use_candle3_only": True, "use_true_mss": True,
     "use_model1": True, "use_ote": True, "use_kod": True, "use_breaker_block": True},
    {"label": "C3_OFF", "use_kill_zone": False, "use_candle3_only": False, "use_true_mss": True,
     "use_model1": True, "use_ote": True, "use_kod": True, "use_breaker_block": True},
    {"label": "M1_Only", "use_kill_zone": False, "use_candle3_only": True, "use_true_mss": False,
     "use_model1": True, "use_ote": False, "use_kod": False, "use_breaker_block": False},
    {"label": "KOD_Only", "use_kill_zone": False, "use_candle3_only": True, "use_true_mss": False,
     "use_model1": False, "use_ote": False, "use_kod": True, "use_breaker_block": False},
    {"label": "OTE_Only", "use_kill_zone": False, "use_candle3_only": True, "use_true_mss": False,
     "use_model1": False, "use_ote": True, "use_kod": False, "use_breaker_block": False},
]

def run_bt(pair, df, cfg, ltf_df=None):
    """Run a single backtest with given config."""
    bt = Backtester(
        initial_capital=10_000, risk_per_trade=0.02,
        use_kill_zone=cfg["use_kill_zone"],
        use_model1=cfg["use_model1"], use_kod=cfg["use_kod"],
        use_ote=cfg["use_ote"], use_breaker_block=cfg["use_breaker_block"],
        use_candle3_only=cfg["use_candle3_only"], use_true_mss=cfg["use_true_mss"],
    )
    res = bt.run(df, pair, stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0], ltf_df=ltf_df)
    return res

print("Running multi-asset backtests...")
print(f"{'Pair':<10} {'Config':<8} {'Trades':<7} {'Win%':<6} {'PnL':<10} {'PF':<5} {'DD%':<6} {'Sharpe':<9} {'AvgW':<8} {'AvgL':<8} {'Time':<6}")
print("=" * 85)

results = []
total = len(ALL_PAIRS) * len(CONFIGS)
run_idx = 0

for pair_name, df in ALL_PAIRS.items():
    for cfg in CONFIGS:
        run_idx += 1
        t0 = time.time()
        try:
            ltf_df = LTF.get(pair_name)
            res = run_bt(pair_name, df, cfg, ltf_df)
            elapsed = time.time() - t0
            r = {
                "pair": pair_name, "config": cfg["label"],
                "trades": res["total_trades"], "win_rate": res["win_rate"],
                "pnl": res["total_pnl"], "pf": res["profit_factor"],
                "dd": res["max_drawdown"], "sharpe": res["sharpe_ratio"],
                "avg_win": res["avg_win"], "avg_loss": res["avg_loss"],
            }
            results.append(r)
            print(f"[{run_idx}/{total}] {pair_name:<10} {cfg['label']:<8} {r['trades']:<7} {r['win_rate']:<6.1f} ${r['pnl']:<7.2f} {r['pf']:<5.2f} {r['dd']:<5.1f}% {r['sharpe']:<8.2f} ${r['avg_win']:<6.2f} ${r['avg_loss']:<6.2f} {elapsed:<5.1f}s")
        except Exception as e:
            print(f"[{run_idx}/{total}] {pair_name:<10} {cfg['label']:<8} ERROR: {e}")
            import traceback
            traceback.print_exc()

# Summary - best config per pair
print("\n\n=== BEST CONFIG PER PAIR (by PnL) ===")
print(f"{'Pair':<10} {'BestCfg':<10} {'Trades':<7} {'Win%':<6} {'PnL':<10} {'PF':<6} {'DD%':<6} {'Sharpe':<8}")
print("=" * 65)

for pair in ALL_PAIRS:
    pair_results = [r for r in results if r["pair"] == pair]
    if not pair_results:
        continue
    best = max(pair_results, key=lambda x: x["pnl"])
    print(f"{pair:<10} {best['config']:<10} {best['trades']:<7} {best['win_rate']:<6.1f} ${best['pnl']:<7.2f} {best['pf']:<6.2f} {best['dd']:<5.1f}% {best['sharpe']:<8.2f}")

# Summary - best pair per config
print("\n\n=== BEST PAIR PER CONFIG (by PnL) ===")
print(f"{'Config':<10} {'BestPair':<10} {'Trades':<7} {'Win%':<6} {'PnL':<10} {'PF':<6} {'DD%':<6} {'Sharpe':<8}")
print("=" * 65)

for cfg_label in [c["label"] for c in CONFIGS]:
    cfg_results = [r for r in results if r["config"] == cfg_label]
    if not cfg_results:
        continue
    best = max(cfg_results, key=lambda x: x["pnl"])
    print(f"{cfg_label:<10} {best['pair']:<10} {best['trades']:<7} {best['win_rate']:<6.1f} ${best['pnl']:<7.2f} {best['pf']:<6.2f} {best['dd']:<5.1f}% {best['sharpe']:<8.2f}")

# LTF comparison for BTC
print("\n\n=== LTF CONFIRMATION TEST (BTC/USDT) ===")
btc_ltf = LTF.get("BTC/USDT")
if btc_ltf is not None:
    print(f"{'Config':<12} {'LTF':<5} {'Trades':<7} {'Win%':<6} {'PnL':<10} {'PF':<6} {'DD%':<6} {'Sharpe':<8}")
    print("=" * 60)
    for cfg in CONFIGS[:3]:
        for use_ltf in [False, True]:
            bt = Backtester(
                initial_capital=10_000, risk_per_trade=0.02,
                use_kill_zone=cfg["use_kill_zone"],
                use_model1=cfg["use_model1"], use_kod=cfg["use_kod"],
                use_ote=cfg["use_ote"], use_breaker_block=cfg["use_breaker_block"],
                use_candle3_only=cfg["use_candle3_only"], use_true_mss=cfg["use_true_mss"],
            )
            t0 = time.time()
            res = bt.run(ALL_PAIRS["BTC/USDT"], "BTC/USDT", stop_loss_pct=0.015,
                        take_profit_ratios=[1.5, 2.0], ltf_df=btc_ltf if use_ltf else None)
            print(f"  {cfg['label']:<10} {'ON' if use_ltf else 'OFF':<5} {res['total_trades']:<7} {res['win_rate']:<6.1f} ${res['total_pnl']:<8.2f} {res['profit_factor']:<6.2f} {res['max_drawdown']:<5.1f}% {res['sharpe_ratio']:<8.2f}")
else:
    print("No LTF data for BTC/USDT")
