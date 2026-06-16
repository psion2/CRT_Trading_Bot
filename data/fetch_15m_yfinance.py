"""Fetch 60 days of 15m data for forex/metals via yfinance."""
import pandas as pd, time
from pathlib import Path

DATA_DIR = Path(__file__).parent / "forex"
DATA_DIR.mkdir(exist_ok=True)

import yfinance as yf

# Note: yfinance 15m is limited to 60 days
TICKERS = {
    "XAU_USD": "GC=F",
    "XAG_USD": "SI=F",
    "EUR_USD": "EURUSD=X",
    "GBP_USD": "GBPUSD=X",
    "AUD_USD": "AUDUSD=X",
    "USD_JPY": "USDJPY=X",
    "USD_CHF": "USDCHF=X",
}

for name, ticker in TICKERS.items():
    fname = DATA_DIR / f"{name}_15m.csv"
    if fname.exists():
        print(f"  EXISTS: {fname.name}")
        continue
    print(f"  Fetching {name} ({ticker}) 15m...", end=" ")
    t0 = time.time()
    try:
        df = yf.download(ticker, period="2mo", interval="15m", progress=False)
        if df is not None and len(df) > 0:
            df = df.droplevel(1, axis=1) if isinstance(df.columns, pd.MultiIndex) else df
            df.index = pd.to_datetime(df.index)
            df.index.name = "timestamp"
            df.columns = [c.lower() for c in df.columns]
            df.to_csv(fname)
            print(f"{len(df)} candles, {df.index[0].date()} to {df.index[-1].date()} ({time.time()-t0:.0f}s)")
        else:
            print("No data")
    except Exception as e:
        print(f"Error: {e}")
