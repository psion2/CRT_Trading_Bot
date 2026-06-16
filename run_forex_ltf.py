"""Rerun forex/metals LTF=ON tests with timezone fix, then update RESULTS.md."""
import sys, time
from pathlib import Path

SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))

from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester
import pandas as pd

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

# HACK: Patch the forex_loader to make indices timezone-naive
# The 4H data has +00:00, 15m data from histdata is naive
# We need the 4H data to be timezone-naive too for searchsorted to work
print("\n=== Fixing timezone in 4H data ===", flush=True)
for p in FOREX_PAIRS:
    df = FOREX_PAIRS[p].copy()
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
        FOREX_PAIRS[p] = df
        print(f"  {p}: made tz-naive ({len(FOREX_PAIRS[p])} candles)", flush=True)

# ============== RUN 1B: Forex/metals LTF=ON ==============
print("\n=== RUN 1B: Forex/metals LTF=ON (tsq_trail) ===", flush=True)
h = f"{'Pair':<10} {'Config':<8} {'Trades':<7} {'Win%':<6} {'PnL':<10} {'PF':<6} {'DD%':<6} {'Sharpe':<8}"
print(h, flush=True)
print("="*75, flush=True)

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
            print(f"[{idx}/{total}] {pair_name:<10} {cfg['label']:<8} {r['total_trades']:<7} {r['win_rate']:<6.1f} ${r['total_pnl']:<+8.2f} {r['profit_factor']:<6.2f} {r['max_drawdown']:<5.1f}% {r['sharpe_ratio']:<8.2f} {el:.1f}s", flush=True)
        except Exception as e:
            print(f"[{idx}/{total}] {pair_name:<10} {cfg['label']:<8} ERROR: {e}", flush=True)
            import traceback; traceback.print_exc()

# ============== RUN 2B: LTF ON vs OFF for forex/metals ==============
print("\n=== RUN 2B: LTF ON vs OFF (forex/metals) ===", flush=True)
ltf_results = []

for pair_name, df in FOREX_PAIRS.items():
    ltf_df = LTF.get(pair_name)
    if ltf_df is None:
        continue
    for cfg in CONFIGS[:4]:
        for use_ltf in [False, True]:
            t0 = time.time()
            try:
                r = run_bt(pair_name, df, cfg, ltf_df if use_ltf else None)
                label = "LTF=ON" if use_ltf else "LTF=OFF"
                ltf_results.append({"pair":pair_name, "config":cfg["label"], "ltf":label,
                    "trades":r["total_trades"], "win_rate":r["win_rate"],
                    "pnl":r["total_pnl"], "pf":r["profit_factor"],
                    "dd":r["max_drawdown"], "sharpe":r["sharpe_ratio"]})
                print(f"  {pair_name:<8} {cfg['label']:<8} {label:<5} {r['total_trades']:<6} {r['win_rate']:<5.1f}% ${r['total_pnl']:<+8.2f} {r['profit_factor']:<5.2f} {r['max_drawdown']:<5.1f}% {r['sharpe_ratio']:<7.2f}", flush=True)
            except Exception as e:
                print(f"  {pair_name:<8} {cfg['label']:<8} ERROR: {e}", flush=True)

# ============== UPDATE RESULTS.MD ==============
import re

results_path = SRC / "RESULTS.md"
with open(results_path, "r", encoding="utf-8") as f:
    content = f.read()

# Build forex Run 1 markdown rows
forex_rows = []
for r in forex_results:
    forex_rows.append(f"| {r['pair']:<8} | {r['config']:<8} | {r['trades']:<5} | {r['win_rate']:<5.1f}% | ${r['pnl']:<+8.2f} | {r['pf']:<5.2f} | {r['dd']:<5.1f}% | {r['sharpe']:<7.2f} | ${r['avg_win']:<7.2f} | ${r['avg_loss']:<7.2f} |")

# Find the Run 1 table and append forex rows before the closing of the table
# The table ends with a blank line after the last row
# Add forex rows just before the summary section
idx_table_end = content.find("\n## Run 2")
if idx_table_end > 0:
    # Insert forex rows right before "## Run 2" section
    insert_point = content.rfind("\n", 0, idx_table_end - 20)
    forex_block = "\n" + "\n".join(forex_rows) + "\n"
    content = content[:insert_point+1] + forex_block + content[insert_point+1:]

# Build LTF comparison rows for forex
ltf_lines = []
for r in ltf_results:
    ltf_lines.append(f"| {r['pair']:<8} | {r['config']:<8} | {r['ltf']:<5} | {r['trades']:<5} | {r['win_rate']:<5.1f}% | ${r['pnl']:<+8.2f} | {r['pf']:<5.2f} | {r['dd']:<5.1f}% | {r['sharpe']:<7.2f} |")

# Find the LTF comparison table end and add forex rows
ltf_section_start = content.find("## Run 2: LTF ON vs OFF")
if ltf_section_start > 0:
    next_section = content.find("\n## ", ltf_section_start + 10)
    if next_section < 0:
        next_section = len(content)
    ltf_table_end = content.rfind("\n", ltf_section_start, next_section)
    ltf_block = "\n" + "\n".join(ltf_lines) + "\n"
    content = content[:ltf_table_end] + ltf_block + content[ltf_table_end:]

# Also add forex to LTF Impact Summary
impact_lines = []
ltf_map = {}
for r in ltf_results:
    k = (r["pair"], r["config"])
    ltf_map.setdefault(k, {})[r["ltf"]] = r
for (p, c), modes in sorted(ltf_map.items()):
    off = modes.get("LTF=OFF")
    on = modes.get("LTF=ON")
    if off and on:
        d = on["pnl"] - off["pnl"]
        impact_lines.append(f"| {p} | {c} | ${off['pnl']:+.2f} | ${on['pnl']:+.2f} | ${d:+.2f} | {off['trades']:.0f} | {on['trades']:.0f} |")

if impact_lines:
    impact_start = content.find("### LTF Impact Summary")
    if impact_start > 0:
        next_header = content.find("## ", impact_start + 5)
        if next_header < 0:
            next_header = len(content)
        # Find the last line of the impact table
        impact_table_end = content.rfind("\n", impact_start, next_header)
        impact_block = "\n" + "\n".join(impact_lines) + "\n"
        content = content[:impact_table_end] + impact_block + content[impact_table_end:]

with open(results_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\nDone! Updated {results_path}", flush=True)
