"""Comprehensive LTF execution test on all forex pairs."""
import sys; from pathlib import Path; import time
sys.path.insert(0, str(Path(__file__).parent))
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

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
            df.index = df.index.tz_localize(None)
        return df
    except:
        return None

LTF = {p: load_ltf(f.replace("/","_")) for p,f in [("EUR/USD","EUR_USD"),("GBP/USD","GBP_USD"),("XAU/USD","XAU_USD"),("XAG/USD","XAG_USD")]}

for p in PAIRS:
    df = PAIRS[p].copy()
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
        PAIRS[p] = df

hdr = f"{'Pair':<10} {'Mode':<12} {'Trades':<7} {'Win%':<7} {'PnL':<12} {'PF':<7} {'DD%':<7} {'Sharpe':<8} {'Diff':<10}"
print(hdr)
print("="*85)

for pair_name, df in PAIRS.items():
    ltf_df = LTF.get(pair_name)
    base_pnl = None

    for mode_name, exec_mode, wsize in [
        ("LTF=OFF", False, 0),
        ("LTF=EXEC(4h)", True, 4),
        ("LTF=EXEC(2h)", True, 2),
    ]:
        t0 = time.time()
        try:
            bt = Backtester(10000, 0.02,
                use_model1=True, use_kod=True, use_ote=True, use_breaker_block=True,
                use_candle3_only=True, use_true_mss=True,
                stop_mode="tsq_trail",
                use_ltf_execution=exec_mode, ltf_window_hours=wsize)
            r = bt.run(df.copy(), pair_name, 0.015, [1.5, 2.0],
                       ltf_df=ltf_df if exec_mode else None)
            el = time.time() - t0

            if not exec_mode:
                base_pnl = r["total_pnl"]
                diff = ""
            else:
                d = r["total_pnl"] - base_pnl
                if d >= 0:
                    diff = f"+${d:.2f}"
                else:
                    diff = f"-${abs(d):.2f}"

            print(
                f"{pair_name:<10} {mode_name:<12} "
                f"{r['total_trades']:<7} {r['win_rate']:<6.1f}% "
                f"${r['total_pnl']:<+9.2f} {r['profit_factor']:<6.2f} "
                f"{r['max_drawdown']:<5.1f}% {r['sharpe_ratio']:<7.3f} "
                f"{diff:<10} {el:.1f}s"
            )
        except Exception as e:
            print(f"{pair_name:<10} {mode_name:<12} ERROR: {e}")
