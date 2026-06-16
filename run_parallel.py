"""Focused multi-asset backtests with parallel execution."""
import sys, time, multiprocessing as mp
from functools import partial
from pathlib import Path

SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))

from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

def worker(pair_name, cfg_label, use_kz, use_m1, use_kod, use_ote, use_bb, use_c3, use_mss, ltf_name):
    loader = ForexDataLoader()
    clean = pair_name.replace("/", "_")
    df = loader.load_forex(clean, "4h")

    ltf_df = None
    if ltf_name:
        try:
            ltf_df = loader.load_forex(ltf_name, "15m")
        except:
            pass

    bt = Backtester(
        initial_capital=10_000, risk_per_trade=0.02,
        use_kill_zone=use_kz, use_model1=use_m1, use_kod=use_kod,
        use_ote=use_ote, use_breaker_block=use_bb,
        use_candle3_only=use_c3, use_true_mss=use_mss,
    )
    res = bt.run(df, pair_name, stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0], ltf_df=ltf_df)
    return (pair_name, cfg_label, res["total_trades"], res["win_rate"], res["total_pnl"],
            res["profit_factor"], res["max_drawdown"], res["sharpe_ratio"],
            res["avg_win"], res["avg_loss"])

if __name__ == "__main__":
    PAIRS = ["BTC/USDT", "ETH/USDT", "EUR/USD", "XAU/USD", "SOL/USDT"]
    CONFIGS = [
        {"label": "Base", "kz":0, "m1":1, "kod":1, "ote":1, "bb":1, "c3":1, "mss":1},
        {"label": "KZ_ON", "kz":1, "m1":1, "kod":1, "ote":1, "bb":1, "c3":1, "mss":1},
        {"label": "C3_OFF", "kz":0, "m1":1, "kod":1, "ote":1, "bb":1, "c3":0, "mss":1},
        {"label": "M1_Only", "kz":0, "m1":1, "kod":0, "ote":0, "bb":0, "c3":1, "mss":0},
        {"label": "KOD_Only","kz":0, "m1":0, "kod":1, "ote":0, "bb":0, "c3":1, "mss":0},
        {"label": "OTE_Only", "kz":0, "m1":0, "kod":0, "ote":1, "bb":0, "c3":1, "mss":0},
    ]

    tasks = []
    for pair in PAIRS:
        for cfg in CONFIGS:
            tasks.append((pair, cfg["label"], cfg["kz"], cfg["m1"], cfg["kod"],
                          cfg["ote"], cfg["bb"], cfg["c3"], cfg["mss"], None))

    for cfg in CONFIGS[:3]:
        tasks.append(("BTC_FULL", cfg["label"]+"_LTF", cfg["kz"], cfg["m1"],
                      cfg["kod"], cfg["ote"], cfg["bb"], cfg["c3"], cfg["mss"], "BTC_USDT"))

    total = len(tasks)
    print(f"Running {total} backtests across {mp.cpu_count()} cores...")

    t_start = time.time()
    completed = 0
    with mp.Pool(processes=min(6, mp.cpu_count())) as pool:
        results = [pool.apply_async(worker, t) for t in tasks]
        for r in results:
            pair, cfg, trades, wr, pnl, pf, dd, sharpe, aw, al = r.get()
            completed += 1
            print(f"[{completed}/{total}] {pair:<15} {cfg:<10} tr={trades:<4} wr={wr:<5.1f}% ${pnl:<8.2f} pf={pf:<5.2f} dd={dd:<5.1f}% ({time.time()-t_start:.0f}s)")

    print(f"\n=== DONE in {time.time()-t_start:.0f}s ===")
