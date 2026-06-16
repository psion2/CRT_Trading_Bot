print("importing...", flush=True)
import sys, time, multiprocessing as mp
from pathlib import Path

print("setting path...", flush=True)
SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))

print("importing project modules...", flush=True)
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

print("imported ok", flush=True)

ALL_PAIRS = {
    "BTC/USDT": "BTC_USDT", "ETH/USDT": "ETH_USDT", "SOL/USDT": "SOL_USDT",
    "EUR/USD": "EUR_USD", "GBP/USD": "GBP_USD", "XAU/USD": "XAU_USD", "XAG/USD": "XAG_USD",
    "AUD/USD": "AUD_USD", "USD/CHF": "USD_CHF", "USD/JPY": "USD_JPY",
}
PAIRS_WITH_LTF = {"BTC/USDT","ETH/USDT","SOL/USDT","EUR/USD","GBP/USD","XAU/USD","XAG/USD"}

CONFIGS = [
    {"label": "Base", "kz":0, "m1":1, "kod":1, "ote":1, "bb":1, "c3":1, "mss":1},
    {"label": "KZ_ON", "kz":1, "m1":1, "kod":1, "ote":1, "bb":1, "c3":1, "mss":1},
    {"label": "C3_OFF","kz":0, "m1":1, "kod":1, "ote":1, "bb":1, "c3":0, "mss":1},
    {"label": "M1_Only","kz":0, "m1":1, "kod":0, "ote":0, "bb":0, "c3":1, "mss":0},
    {"label": "KOD_Only","kz":0, "m1":0, "kod":1, "ote":0, "bb":0, "c3":1, "mss":0},
    {"label": "OTE_Only","kz":0, "m1":0, "kod":0, "ote":1, "bb":0, "c3":1, "mss":0},
]

print("starting worker function...", flush=True)

def worker(pair_label, cfg, stop_mode, use_ltf):
    from data.forex_loader import ForexDataLoader
    from backtest.backtester import Backtester
    fname = ALL_PAIRS[pair_label]
    loader = ForexDataLoader()
    df = loader.load_forex(fname, "4h")
    ltf_df = None
    if use_ltf and pair_label in PAIRS_WITH_LTF:
        try:
            ltf_df = loader.load_forex(fname, "15m")
        except:
            pass
    bt = Backtester(
        initial_capital=10_000, risk_per_trade=0.02,
        use_kill_zone=bool(cfg["kz"]), use_model1=bool(cfg["m1"]),
        use_kod=bool(cfg["kod"]), use_ote=bool(cfg["ote"]),
        use_breaker_block=bool(cfg["bb"]),
        use_candle3_only=bool(cfg["c3"]), use_true_mss=bool(cfg["mss"]),
        stop_mode=stop_mode,
    )
    res = bt.run(df, pair_label, stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0], ltf_df=ltf_df)
    return {
        "pair": pair_label, "config": cfg["label"], "stop_mode": stop_mode,
        "trades": res["total_trades"], "win_rate": res["win_rate"],
        "pnl": res["total_pnl"], "pf": res["profit_factor"],
        "dd": res["max_drawdown"], "sharpe": res["sharpe_ratio"],
        "avg_win": res["avg_win"], "avg_loss": res["avg_loss"],
    }

print("entering main...", flush=True)

if __name__ == "__main__":
    print("in main block", flush=True)
    t_start = time.time()
    
    print(f"Building tasks: {len(ALL_PAIRS)} pairs × {len(CONFIGS)} configs", flush=True)
    tasks1 = []
    for pair in ALL_PAIRS:
        for cfg in CONFIGS:
            use_ltf = pair in PAIRS_WITH_LTF
            tasks1.append((pair, cfg, "tsq_trail", use_ltf))
    print(f"Tasks: {len(tasks1)}", flush=True)
    
    print("Starting pool...", flush=True)
    results1 = []
    with mp.Pool(processes=min(4, mp.cpu_count())) as pool:
        rs = [pool.apply_async(worker, t) for t in tasks1]
        done = 0
        for r in rs:
            res = r.get()
            results1.append(res)
            done += 1
            print(f"[{done}/{len(tasks1)}] {res['pair']:<10} {res['config']:<8} tr={res['trades']:<5} wr={res['win_rate']:<5.1f}% ${res['pnl']:<+8.2f} dd={res['dd']:<5.1f}% ({time.time()-t_start:.0f}s)", flush=True)
    
    print("DONE", flush=True)
