"""Run 1B only: forex/metals LTF=ON with all 6 configs, save results."""
import sys, time, json
from pathlib import Path

SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))

from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

print("Loading data...", flush=True)
loader = ForexDataLoader()

FOREX_PAIRS = {
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
for p in FOREX_PAIRS:
    df = FOREX_PAIRS[p].copy()
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
        FOREX_PAIRS[p] = df

CONFIGS = [
    {"label": "Base", "kz":0, "m1":1, "kod":1, "ote":1, "bb":1, "c3":1, "mss":1},
    {"label": "KZ_ON", "kz":1, "m1":1, "kod":1, "ote":1, "bb":1, "c3":1, "mss":1},
    {"label": "C3_OFF","kz":0, "m1":1, "kod":1, "ote":1, "bb":1, "c3":0, "mss":1},
    {"label": "M1_Only","kz":0, "m1":1, "kod":0, "ote":0, "bb":0, "c3":1, "mss":0},
    {"label": "KOD_Only","kz":0, "m1":0, "kod":1, "ote":0, "bb":0, "c3":1, "mss":0},
    {"label": "OTE_Only","kz":0, "m1":0, "kod":0, "ote":1, "bb":0, "c3":1, "mss":0},
]

def run_bt(pair, df, cfg, ltf_df=None):
    bt = Backtester(initial_capital=10_000, risk_per_trade=0.02,
        use_kill_zone=bool(cfg["kz"]), use_model1=bool(cfg["m1"]),
        use_kod=bool(cfg["kod"]), use_ote=bool(cfg["ote"]),
        use_breaker_block=bool(cfg["bb"]),
        use_candle3_only=bool(cfg["c3"]), use_true_mss=bool(cfg["mss"]),
        stop_mode="tsq_trail")
    return bt.run(df, pair, stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0], ltf_df=ltf_df)

print("\n=== RUN 1B: Forex/metals LTF=ON (tsq_trail) ===", flush=True)
h = f"{'Pair':<10} {'Config':<8} {'Trades':<7} {'Win%':<6} {'PnL':<10} {'PF':<6} {'DD%':<6} {'Sharpe':<8} {'AvgWin':<9} {'AvgLoss':<9}"
print(h, flush=True)
print("="*90, flush=True)

forex_results = []
total = len(FOREX_PAIRS) * len(CONFIGS)
idx = 0

for pair_name, df in FOREX_PAIRS.items():
    ltf_df = LTF.get(pair_name)
    for cfg in CONFIGS:
        idx += 1
        t0 = time.time()
        try:
            r = run_bt(pair_name, df, cfg, ltf_df)
            el = time.time() - t0
            forex_results.append({"pair":pair_name, "config":cfg["label"],
                "trades":r["total_trades"], "win_rate":r["win_rate"],
                "pnl":r["total_pnl"], "pf":r["profit_factor"],
                "dd":r["max_drawdown"], "sharpe":r["sharpe_ratio"],
                "avg_win":r["avg_win"], "avg_loss":r["avg_loss"]})
            print(f"[{idx}/{total}] {pair_name:<10} {cfg['label']:<8} {r['total_trades']:<7} {r['win_rate']:<6.1f} ${r['total_pnl']:<+8.2f} {r['profit_factor']:<6.2f} {r['max_drawdown']:<5.1f}% {r['sharpe_ratio']:<8.2f} ${r['avg_win']:<7.2f} ${r['avg_loss']:<7.2f} {el:.0f}s", flush=True)
        except Exception as e:
            print(f"[{idx}/{total}] {pair_name:<10} {cfg['label']:<8} ERROR: {e}", flush=True)
            import traceback; traceback.print_exc()

with open("forex_run1b_results.json", "w") as f:
    json.dump(forex_results, f, indent=2)
print(f"\nDone! {len(forex_results)} results saved to forex_run1b_results.json", flush=True)
