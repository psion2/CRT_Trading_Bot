"""Fetch 4H and 15min data for all target assets."""
import pandas as pd
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent / "forex"
DATA_DIR.mkdir(exist_ok=True)

# === Crypto via CCXT Binance ===
import ccxt
binance = ccxt.binance()
binance.load_markets()

CRYPTO_PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
SINCE_MS = int(pd.Timestamp("2024-03-01").timestamp() * 1000)

def fetch_pair_ccxt(pair, tf, limit=1000):
    all_ohlcv = []
    since = SINCE_MS
    for _ in range(50):
        try:
            ohlcv = binance.fetch_ohlcv(pair, tf, since=since, limit=limit)
            if not ohlcv:
                break
            all_ohlcv.extend(ohlcv)
            since = ohlcv[-1][0] + 1
            if len(ohlcv) < limit:
                break
        except Exception as e:
            print(f"  Error: {e}")
            break
    if not all_ohlcv:
        return None
    df = pd.DataFrame(all_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    df = df[~df.index.duplicated(keep="last")]
    return df

for pair in CRYPTO_PAIRS:
    clean = pair.replace("/", "_")
    for tf in ["4h", "15m"]:
        fname = DATA_DIR / f"{clean}_{tf}.csv"
        if fname.exists():
            print(f"  Already exists: {fname}")
            continue
        print(f"  Fetching {pair} {tf}...")
        t0 = time.time()
        df = fetch_pair_ccxt(pair, tf)
        if df is not None:
            df.to_csv(fname)
            print(f"    {len(df)} candles, took {time.time()-t0:.1f}s, range {df.index[0]} to {df.index[-1]}")
        else:
            print(f"    FAILED")

# === Metals via yfinance ===
import yfinance as yf
METALS = {"XAU_USD": "GC=F", "XAG_USD": "SI=F"}

for name, ticker in METALS.items():
    for tf_suffix, interval in [("4h", "4h"), ("15m", "15m")]:
        fname = DATA_DIR / f"{name}_{tf_suffix}.csv"
        if fname.exists():
            print(f"  Already exists: {fname}")
            continue
        print(f"  Fetching {name} ({ticker}) {tf_suffix}...")
        t0 = time.time()
        try:
            df = yf.download(ticker, period="2y", interval=interval, progress=False)
            if df is not None and len(df) > 0:
                df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
                df.index = pd.to_datetime(df.index)
                df.index.name = "timestamp"
                df.columns = [c.lower() for c in df.columns]
                df.to_csv(fname)
                print(f"    {len(df)} candles, took {time.time()-t0:.1f}s")
            else:
                print(f"    No data returned")
        except Exception as e:
            print(f"    Error: {e}")

# === Forex 15min data via yfinance ===
FOREX_15M = {
    "EUR_USD": "EURUSD=X",
    "GBP_USD": "GBPUSD=X",
}

for name, ticker in FOREX_15M.items():
    fname = DATA_DIR / f"{name}_15m.csv"
    if fname.exists():
        print(f"  Already exists: {fname}")
        continue
    print(f"  Fetching {name} 15m...")
    t0 = time.time()
    try:
        df = yf.download(ticker, period="2y", interval="15m", progress=False)
        if df is not None and len(df) > 0:
            df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
            df.index = pd.to_datetime(df.index)
            df.index.name = "timestamp"
            df.columns = [c.lower() for c in df.columns]
            df.to_csv(fname)
            print(f"    {len(df)} candles, took {time.time()-t0:.1f}s")
        else:
            print(f"    No data returned")
    except Exception as e:
        print(f"    Error: {e}")

print("\nDone! Available files:")
for f in sorted(DATA_DIR.glob("*.csv")):
    size_kb = f.stat().st_size / 1024
    print(f"  {f.name} ({size_kb:.0f}KB)")
