"""Extended multi-asset backtest runner with LTF for all pairs + tsq_trail."""
import sys, time, gc
from pathlib import Path

SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))

from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester
import pandas as pd
import numpy as np

print("Loading data...", flush=True)
loader = ForexDataLoader()

# Load all 4H data
ALL_PAIRS = {
    "BTC/USDT": loader.load_forex("BTC_USDT", "4h"),
    "ETH/USDT": loader.load_forex("ETH_USDT", "4h"),
    "SOL/USDT": loader.load_forex("SOL_USDT", "4h"),
    "EUR/USD": loader.load_forex("EUR_USD", "4h"),
    "GBP/USD": loader.load_forex("GBP_USD", "4h"),
    "XAU/USD": loader.load_forex("XAU_USD", "4h"),
    "XAG/USD": loader.load_forex("XAG_USD", "4h"),
    "AUD/USD": loader.load_forex("AUD_USD", "4h"),
    "USD/CHF": loader.load_forex("USD_CHF", "4h"),
    "USD/JPY": loader.load_forex("USD_JPY", "4h"),
}
print(f"Loaded {len(ALL_PAIRS)} pairs", flush=True)

# Load 15m LTF data for all available
def load_ltf(name):
    try:
        df = loader.load_forex(name, "15m")
        print(f"  15m {name}: {len(df)} candles", flush=True)
        return df
    except Exception as e:
        print(f"  No 15m for {name}", flush=True)
        return None

LTF = {}
for pair_label, fname in [("BTC/USDT","BTC_USDT"),("ETH/USDT","ETH_USDT"),("SOL/USDT","SOL_USDT"),
                           ("EUR/USD","EUR_USD"),("GBP/USD","GBP_USD"),
                           ("XAU/USD","XAU_USD"),("XAG/USD","XAG_USD")]:
    LTF[pair_label] = load_ltf(fname)

CONFIGS = [
    {"label": "Base", "kz":0, "m1":1, "kod":1, "ote":1, "bb":1, "c3":1, "mss":1},
    {"label": "KZ_ON", "kz":1, "m1":1, "kod":1, "ote":1, "bb":1, "c3":1, "mss":1},
    {"label": "C3_OFF","kz":0, "m1":1, "kod":1, "ote":1, "bb":1, "c3":0, "mss":1},
    {"label": "M1_Only","kz":0, "m1":1, "kod":0, "ote":0, "bb":0, "c3":1, "mss":0},
    {"label": "KOD_Only","kz":0, "m1":0, "kod":1, "ote":0, "bb":0, "c3":1, "mss":0},
    {"label": "OTE_Only","kz":0, "m1":0, "kod":0, "ote":1, "bb":0, "c3":1, "mss":0},
]

def run_bt(pair, df, cfg, ltf_df=None, stop_mode="tsq_trail"):
    bt = Backtester(
        initial_capital=10_000, risk_per_trade=0.02,
        use_kill_zone=bool(cfg["kz"]), use_model1=bool(cfg["m1"]),
        use_kod=bool(cfg["kod"]), use_ote=bool(cfg["ote"]),
        use_breaker_block=bool(cfg["bb"]),
        use_candle3_only=bool(cfg["c3"]), use_true_mss=bool(cfg["mss"]),
        stop_mode=stop_mode,
    )
    return bt.run(df, pair, stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0], ltf_df=ltf_df)

# ============== RUN 1: ALL PAIRS × ALL CONFIGS (LTF=ON, tsq_trail) ==============
print("\n=== RUN 1: All configs × all pairs (tsq_trail, LTF=ON) ===", flush=True)
h = f"{'Pair':<10} {'Config':<8} {'Trades':<7} {'Win%':<6} {'PnL':<10} {'PF':<6} {'DD%':<6} {'Sharpe':<8} {'Time':<6}"
print(h, flush=True)
print("="*75, flush=True)

res1 = []
total = len(ALL_PAIRS) * len(CONFIGS)
idx = 0

for pair_name, df in ALL_PAIRS.items():
    ltf_df = LTF.get(pair_name)
    for cfg in CONFIGS:
        idx += 1
        t0 = time.time()
        try:
            r = run_bt(pair_name, df, cfg, ltf_df, stop_mode="tsq_trail")
            el = time.time() - t0
            res1.append({"pair":pair_name, "config":cfg["label"],
                "trades":r["total_trades"], "win_rate":r["win_rate"],
                "pnl":r["total_pnl"], "pf":r["profit_factor"],
                "dd":r["max_drawdown"], "sharpe":r["sharpe_ratio"],
                "avg_win":r["avg_win"], "avg_loss":r["avg_loss"]})
            print(f"[{idx}/{total}] {pair_name:<10} {cfg['label']:<8} {r['total_trades']:<7} {r['win_rate']:<6.1f} ${r['total_pnl']:<+8.2f} {r['profit_factor']:<6.2f} {r['max_drawdown']:<5.1f}% {r['sharpe_ratio']:<8.2f} {el:.1f}s", flush=True)
        except Exception as e:
            print(f"[{idx}/{total}] {pair_name:<10} {cfg['label']:<8} ERROR: {e}", flush=True)
            import traceback; traceback.print_exc()

# ============== RUN 2: LTF ON vs OFF for pairs with 15m ==============
print("\n=== RUN 2: LTF ON vs OFF (tsq_trail) ===", flush=True)
h2 = f"{'Pair':<10} {'Cfg':<8} {'Mode':<5} {'Trades':<6} {'Win%':<5} {'PnL':<10} {'PF':<5} {'DD%':<5} {'Sharpe':<7}"
print(h2, flush=True)
print("="*70, flush=True)

res2 = []
for pair_name, df in ALL_PAIRS.items():
    ltf_df = LTF.get(pair_name)
    if ltf_df is None:
        continue
    for cfg in CONFIGS[:4]:
        for use_ltf in [False, True]:
            t0 = time.time()
            try:
                r = run_bt(pair_name, df, cfg, ltf_df if use_ltf else None, stop_mode="tsq_trail")
                label = "LTF=ON" if use_ltf else "LTF=OFF"
                res2.append({"pair":pair_name, "config":cfg["label"], "ltf":label,
                    "trades":r["total_trades"], "win_rate":r["win_rate"],
                    "pnl":r["total_pnl"], "pf":r["profit_factor"],
                    "dd":r["max_drawdown"], "sharpe":r["sharpe_ratio"]})
                print(f"  {pair_name:<8} {cfg['label']:<8} {label:<5} {r['total_trades']:<6} {r['win_rate']:<5.1f}% ${r['total_pnl']:<+8.2f} {r['profit_factor']:<5.2f} {r['max_drawdown']:<5.1f}% {r['sharpe_ratio']:<7.2f}", flush=True)
            except Exception as e:
                print(f"  {pair_name:<8} {cfg['label']:<8} ERROR: {e}", flush=True)

# ============== GENERATE RESULTS.MD ==============
print("\nGenerating RESULTS.md...", flush=True)

def md_table(rows, cols):
    if not rows: return ""
    h = "| " + " | ".join(cols) + " |"
    s = "| " + " | ".join(["---"]*len(cols)) + " |"
    lines = [h, s]
    for r in rows:
        vals = []
        for c in cols:
            v = r.get(c, "")
            if isinstance(v, float):
                if c == "pnl": vals.append(f"${v:+.2f}")
                elif c == "dd": vals.append(f"{v:.1f}%")
                elif c == "trades": vals.append(f"{v:.0f}")
                elif c == "win_rate": vals.append(f"{v:.1f}%")
                else: vals.append(f"{v:.2f}")
            else: vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)

lines = []
lines.append("# CRT Trading Bot - Comprehensive Backtest Results")
lines.append("")
lines.append(f"*Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}*")
lines.append("")
lines.append("## Summary")
lines.append("")
lines.append(f"- **Pairs:** {', '.join(sorted(ALL_PAIRS.keys()))}")
lines.append(f"- **Timeframe:** 4H (primary), 15m (LTF confirmation)")
lines.append(f"- **Capital:** $10,000 simulated, 2% risk per trade")
lines.append(f"- **Stop Loss:** 1.5%, **Take Profit:** 1.5x / 2.0x")
lines.append(f"- **Stop Mode:** tsq_trail (TSQ trailing stops)")
lines.append(f"- **LTF 15m data (2016-2025):** EUR/USD, GBP/USD, XAU/USD, XAG/USD")
lines.append(f"- **LTF 15m data (CCXT Binance):** BTC/USDT, ETH/USDT, SOL/USDT")
lines.append("")
lines.append("## Run 1: All Configs × All Pairs (tsq_trail, LTF=ON)")
lines.append("")
lines.append(md_table(res1, ["pair","config","trades","win_rate","pnl","pf","dd","sharpe","avg_win","avg_loss"]))
lines.append("")

# Best per pair
lines.append("### Best Config Per Pair (by PnL)")
lines.append("")
best_pair = []
for p in ALL_PAIRS:
    pr = [r for r in res1 if r["pair"] == p]
    if pr:
        best_pair.append(max(pr, key=lambda x: x["pnl"]))
lines.append(md_table(best_pair, ["pair","config","trades","win_rate","pnl","pf","dd","sharpe"]))
lines.append("")

# Best per config
lines.append("### Best Pair Per Config (by PnL)")
lines.append("")
best_cfg = []
for c in CONFIGS:
    cr = [r for r in res1 if r["config"] == c["label"]]
    if cr:
        best_cfg.append(max(cr, key=lambda x: x["pnl"]))
lines.append(md_table(best_cfg, ["config","pair","trades","win_rate","pnl","pf","dd","sharpe"]))
lines.append("")

# Run 2: LTF comparison
lines.append("## Run 2: LTF ON vs OFF Comparison (tsq_trail)")
lines.append("")
lines.append(md_table(res2, ["pair","config","ltf","trades","win_rate","pnl","pf","dd","sharpe"]))
lines.append("")

# LTF impact
lines.append("### LTF Impact Summary")
lines.append("")
lines.append("| Pair | Config | LTF=OFF PnL | LTF=ON PnL | Delta | Trades OFF | Trades ON |")
lines.append("| --- | --- | --- | --- | --- | --- | --- |")
ltf_map = {}
for r in res2:
    k = (r["pair"], r["config"])
    ltf_map.setdefault(k, {})[r["ltf"]] = r
for (p, c), modes in sorted(ltf_map.items()):
    off = modes.get("LTF=OFF")
    on = modes.get("LTF=ON")
    if off and on:
        d = on["pnl"] - off["pnl"]
        lines.append(f"| {p} | {c} | ${off['pnl']:+.2f} | ${on['pnl']:+.2f} | ${d:+.2f} | {off['trades']:.0f} | {on['trades']:.0f} |")
lines.append("")

# Key observations placeholder
lines.append("## Key Observations")
lines.append("")
lines.append("TBD after analysis")
lines.append("")

out_path = SRC / "RESULTS.md"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\nDone! Results saved to {out_path}", flush=True)
