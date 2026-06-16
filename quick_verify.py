"""Quick verify: crypto only, compare with old results."""
import sys, time
from pathlib import Path
SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

loader = ForexDataLoader()
PAIRS = {p: loader.load_forex(r, "4h") for p, r in [("BTC/USDT","BTC_USDT"),("ETH/USDT","ETH_USDT"),("SOL/USDT","SOL_USDT")]}

CONFIGS = [
    {"label":"Base","kz":0,"m1":1,"kod":1,"ote":1,"bb":1,"c3":1,"mss":1},
    {"label":"M1_Only","kz":0,"m1":1,"kod":0,"ote":0,"bb":0,"c3":1,"mss":0},
    {"label":"KOD_Only","kz":0,"m1":0,"kod":1,"ote":0,"bb":0,"c3":1,"mss":0},
]

def run_bt(pair, df, cfg):
    bt = Backtester(10_000, 0.02, bool(cfg["kz"]), bool(cfg["m1"]), bool(cfg["kod"]),
        bool(cfg["ote"]), bool(cfg["bb"]), bool(cfg["c3"]), bool(cfg["mss"]), "tsq_trail")
    return bt.run(df, pair, 0.015, [1.5, 2.0])

OLD = {("BTC/USDT","Base"):91198.47, ("BTC/USDT","M1_Only"):617.69,
       ("ETH/USDT","Base"):66266.26, ("ETH/USDT","M1_Only"):2321.71,
       ("SOL/USDT","Base"):239087.58, ("SOL/USDT","M1_Only"):11597.36}

for pair_name, df in PAIRS.items():
    for cfg in CONFIGS:
        r = run_bt(pair_name, df, cfg)
        old = OLD.get((pair_name, cfg["label"]), None)
        delta = f"({((r['total_pnl']/old)-1)*100:+.0f}%)" if old else ""
        print(f"{pair_name:<10} {cfg['label']:<8} trades={r['total_trades']:<5} PnL=${r['total_pnl']:<+9.2f} old=${old:<+9.2f} {delta}", flush=True)
