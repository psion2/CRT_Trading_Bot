"""Test price-level fixes: crypto pairs × 6 configs, LTF=OFF."""
import sys, time, json
from pathlib import Path

SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))

from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

print("Loading crypto data...", flush=True)
loader = ForexDataLoader()

CRYPTO_PAIRS = {
    "BTC/USDT": loader.load_forex("BTC_USDT", "4h"),
    "ETH/USDT": loader.load_forex("ETH_USDT", "4h"),
    "SOL/USDT": loader.load_forex("SOL_USDT", "4h"),
}

CONFIGS = [
    {"label": "Base", "kz": 0, "m1": 1, "kod": 1, "ote": 1, "bb": 1, "c3": 1, "mss": 1},
    {"label": "KZ_ON", "kz": 1, "m1": 1, "kod": 1, "ote": 1, "bb": 1, "c3": 1, "mss": 1},
    {"label": "C3_OFF", "kz": 0, "m1": 1, "kod": 1, "ote": 1, "bb": 1, "c3": 0, "mss": 1},
    {"label": "M1_Only", "kz": 0, "m1": 1, "kod": 0, "ote": 0, "bb": 0, "c3": 1, "mss": 0},
    {"label": "KOD_Only", "kz": 0, "m1": 0, "kod": 1, "ote": 0, "bb": 0, "c3": 1, "mss": 0},
    {"label": "OTE_Only", "kz": 0, "m1": 0, "kod": 0, "ote": 1, "bb": 0, "c3": 1, "mss": 0},
]

def run_bt(pair, df, cfg):
    bt = Backtester(initial_capital=10_000, risk_per_trade=0.02,
        use_kill_zone=bool(cfg["kz"]), use_model1=bool(cfg["m1"]),
        use_kod=bool(cfg["kod"]), use_ote=bool(cfg["ote"]),
        use_breaker_block=bool(cfg["bb"]),
        use_candle3_only=bool(cfg["c3"]), use_true_mss=bool(cfg["mss"]),
        stop_mode="tsq_trail")
    return bt.run(df, pair, stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0])

print(f"{'Pair':<10} {'Config':<8} {'Trades':<6} {'Win%':<6} {'PnL':<12} {'PF':<6} {'DD%':<6} {'Sharpe':<7} {'Time':<5}")
print("="*75, flush=True)

results = []
total = len(CRYPTO_PAIRS) * len(CONFIGS)
idx = 0

for pair_name, df in CRYPTO_PAIRS.items():
    for cfg in CONFIGS:
        idx += 1
        t0 = time.time()
        try:
            r = run_bt(pair_name, df, cfg)
            el = time.time() - t0
            results.append({"pair": pair_name, "config": cfg["label"],
                "trades": r["total_trades"], "win_rate": r["win_rate"],
                "pnl": r["total_pnl"], "pf": r["profit_factor"],
                "dd": r["max_drawdown"], "sharpe": r["sharpe_ratio"]})
            print(f"[{idx}/{total}] {pair_name:<10} {cfg['label']:<8} {r['total_trades']:<6} {r['win_rate']:<6.1f} ${r['total_pnl']:<+9.2f} {r['profit_factor']:<6.2f} {r['max_drawdown']:<5.1f}% {r['sharpe_ratio']:<7.2f} {el:.0f}s", flush=True)
        except Exception as e:
            print(f"[{idx}/{total}] {pair_name:<10} {cfg['label']:<8} ERROR: {e}", flush=True)
            import traceback; traceback.print_exc()

with open(SRC / "test_price_fix_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved {len(results)} results to test_price_fix_results.json", flush=True)

# Compare with old LTF=OFF results
old = {
    ("BTC/USDT", "Base"): (1374, 91198.47),
    ("BTC/USDT", "KZ_ON"): (411, 5544.82),
    ("BTC/USDT", "C3_OFF"): (1528, 127131.43),
    ("BTC/USDT", "M1_Only"): (570, 617.69),
    ("ETH/USDT", "Base"): (1360, 66266.26),
    ("ETH/USDT", "KZ_ON"): (408, 4018.07),
    ("ETH/USDT", "C3_OFF"): (1515, 55435.34),
    ("ETH/USDT", "M1_Only"): (550, 2321.71),
    ("SOL/USDT", "Base"): (1477, 239087.58),
    ("SOL/USDT", "KZ_ON"): (433, 24635.63),
    ("SOL/USDT", "C3_OFF"): (1689, 562432.93),
    ("SOL/USDT", "M1_Only"): (629, 11597.36),
}

print("\n=== Comparison: Old LTF=OFF vs New Price-Fix ===\n", flush=True)
print(f"{'Pair':<10} {'Config':<8} {'Old Trades':<9} {'New Trades':<9} {'Old PnL':<12} {'New PnL':<12} {'Delta':<12}")
print("="*75, flush=True)
for r in results:
    k = (r["pair"], r["config"])
    if k in old:
        o = old[k]
        d = r["pnl"] - o[1]
        print(f"{r['pair']:<10} {r['config']:<8} {o[0]:<9} {r['trades']:<9} ${o[1]:<+9.2f} ${r['pnl']:<+9.2f} ${d:<+9.2f}", flush=True)

print("\nDone!", flush=True)
