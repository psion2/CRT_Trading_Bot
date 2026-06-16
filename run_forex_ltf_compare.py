"""Run 2B only: LTF ON vs OFF comparison for forex/metals (timezone fixed)."""
import sys, time, json
from pathlib import Path

SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))

from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester
import pandas as pd

print("Loading data...", flush=True)
loader = ForexDataLoader()

PAIRS = {
    "EUR/USD": loader.load_forex("EUR_USD", "4h"),
    "GBP/USD": loader.load_forex("GBP_USD", "4h"),
    "XAU/USD": loader.load_forex("XAU_USD", "4h"),
    "XAG/USD": loader.load_forex("XAG_USD", "4h"),
}

def load_ltf(name):
    try:
        df = loader.load_forex(name, "15m")
        if df is not None and df.index.tz is not None:
            df.index = df.index.tz_convert("UTC")
        print(f"  15m {name}: {len(df)} candles", flush=True)
        return df
    except Exception as e:
        print(f"  No 15m for {name}: {e}", flush=True)
        return None

LTF = {p: load_ltf(f.replace("/","_")) for p, f in [("EUR/USD","EUR_USD"),("GBP/USD","GBP_USD"),("XAU/USD","XAU_USD"),("XAG/USD","XAG_USD")]}

# Make 4H data tz-naive
print("\nFixing timezone in 4H data...", flush=True)
for p in PAIRS:
    df = PAIRS[p].copy()
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
        PAIRS[p] = df
        print(f"  {p}: made tz-naive", flush=True)

CONFIGS = [
    {"label": "Base", "kz":0, "m1":1, "kod":1, "ote":1, "bb":1, "c3":1, "mss":1},
    {"label": "KZ_ON", "kz":1, "m1":1, "kod":1, "ote":1, "bb":1, "c3":1, "mss":1},
    {"label": "C3_OFF","kz":0, "m1":1, "kod":1, "ote":1, "bb":1, "c3":0, "mss":1},
    {"label": "M1_Only","kz":0, "m1":1, "kod":0, "ote":0, "bb":0, "c3":1, "mss":0},
]

def run_bt(pair, df, cfg, ltf_df=None):
    bt = Backtester(initial_capital=10_000, risk_per_trade=0.02,
        use_kill_zone=bool(cfg["kz"]), use_model1=bool(cfg["m1"]),
        use_kod=bool(cfg["kod"]), use_ote=bool(cfg["ote"]),
        use_breaker_block=bool(cfg["bb"]),
        use_candle3_only=bool(cfg["c3"]), use_true_mss=bool(cfg["mss"]),
        stop_mode="tsq_trail")
    return bt.run(df, pair, stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0], ltf_df=ltf_df)

print("\n=== RUN 2B: LTF ON vs OFF (forex/metals) ===", flush=True)
h = f"{'Pair':<8} {'Config':<8} {'Mode':<8} {'Trades':<6} {'Win%':<5} {'PnL':<10} {'PF':<6} {'DD%':<6} {'Sharpe':<7}"
print(h, flush=True)
print("="*80, flush=True)

ltf_results = []
total = len(PAIRS) * len(CONFIGS) * 2
idx = 0

for pair_name, df in PAIRS.items():
    ltf_df = LTF.get(pair_name)
    if ltf_df is None:
        continue
    for cfg in CONFIGS:
        for use_ltf in [False, True]:
            idx += 1
            t0 = time.time()
            try:
                r = run_bt(pair_name, df, cfg, ltf_df if use_ltf else None)
                label = "LTF=ON" if use_ltf else "LTF=OFF"
                ltf_results.append({"pair":pair_name, "config":cfg["label"], "ltf":label,
                    "trades":r["total_trades"], "win_rate":r["win_rate"],
                    "pnl":r["total_pnl"], "pf":r["profit_factor"],
                    "dd":r["max_drawdown"], "sharpe":r["sharpe_ratio"]})
                el = time.time() - t0
                print(f"[{idx}/{total}] {pair_name:<8} {cfg['label']:<8} {label:<8} {r['total_trades']:<6} {r['win_rate']:<5.1f}% ${r['total_pnl']:<+8.2f} {r['profit_factor']:<5.2f} {r['max_drawdown']:<5.1f}% {r['sharpe_ratio']:<7.2f} {el:.0f}s", flush=True)
            except Exception as e:
                print(f"[{idx}/{total}] {pair_name:<8} {cfg['label']:<8} ERROR: {e}", flush=True)
                import traceback; traceback.print_exc()

with open("forex_ltf_compare.json", "w") as f:
    json.dump(ltf_results, f, indent=2)
print(f"\nDone! {len(ltf_results)} results saved to forex_ltf_compare.json", flush=True)
