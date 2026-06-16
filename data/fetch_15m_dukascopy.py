"""Fetch 15m data for forex/metals from Dukascopy free datafeed."""
import sys, time, struct, lzma, requests
from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).parent / "forex"
DATA_DIR.mkdir(exist_ok=True)

INSTRUMENTS = {
    "XAU_USD": "XAUUSD",
    "XAG_USD": "XAGUSD",
    "EUR_USD": "EURUSD",
    "GBP_USD": "GBPUSD",
    "AUD_USD": "AUDUSD",
    "USD_JPY": "USDJPY",
    "USD_CHF": "USDCHF",
}

START = pd.Timestamp("2024-03-01")
END = pd.Timestamp("2026-05-29")
TICKER_URL = "https://datafeed.dukascopy.com/datafeed/{inst}/{Y}/{m:02d}/{d:02d}/{h:02d}h_ticks.bi5"

def fetch_day(inst, year, month, day):
    """Download and parse one day of tick data from Dukascopy."""
    ticks = []
    for hour in range(24):
        url = TICKER_URL.format(inst=inst, Y=year, m=month, d=day, h=hour)
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                continue
            raw = lzma.decompress(resp.content)
        except:
            continue
        for i in range(0, len(raw), 20):
            if i + 20 > len(raw):
                break
            t, ask, bid, _, _ = struct.unpack('>iiff', raw[i:i+20])
            if ask > 0 and bid > 0:
                ticks.append((t + hour * 3600000, (ask + bid) / 2))
    if not ticks:
        return pd.DataFrame()
    df = pd.DataFrame(ticks, columns=["ms", "price"])
    df["dt"] = pd.to_datetime(df["ms"], unit="ms")
    df.set_index("dt", inplace=True)
    df.sort_index(inplace=True)
    return df

def resample_ohlc(df):
    """Resample tick/1m data to 15m OHLCV."""
    return df["price"].resample("15min").ohlc().dropna()

def fetch_15m(name, inst, start, end):
    fname = DATA_DIR / f"{name}_15m.csv"
    if fname.exists():
        print(f"  EXISTS: {fname.name}")
        return

    print(f"  Fetching {name} ({inst}) {start.date()} to {end.date()}...")
    t0 = time.time()
    all_1m = []
    current = start
    while current < end:
        yr, mo, dy = current.year, current.month, current.day
        day_df = fetch_day(inst, yr, mo, dy)
        if not day_df.empty:
            all_1m.append(day_df)
        current += pd.Timedelta(days=1)
        if len(all_1m) % 30 == 0 and all_1m:
            print(f"    ... {len(all_1m)} days, latest: {current.date()} ({time.time()-t0:.0f}s)")

    if not all_1m:
        print(f"    NO DATA")
        return

    ticks = pd.concat(all_1m)
    ticks = ticks[~ticks.index.duplicated(keep="first")]
    ticks.sort_index(inplace=True)

    ohlc_15m = ticks["price"].resample("15min").agg({
        "open": "first", "high": "max", "low": "min", "close": "last"
    }).dropna()

    df_out = pd.DataFrame({
        "open": ohlc_15m["open"].values,
        "high": ohlc_15m["high"].values,
        "low": ohlc_15m["low"].values,
        "close": ohlc_15m["close"].values,
    }, index=ohlc_15m.index)
    df_out.index.name = "timestamp"
    df_out.to_csv(fname)
    elapsed = time.time() - t0
    print(f"    {len(df_out)} candles ({len(ticks)} ticks), {elapsed:.0f}s, range {df_out.index[0]} to {df_out.index[-1]}")

print("Dukascopy 15m Data Fetcher")
print("=" * 50)
for name, inst in INSTRUMENTS.items():
    fetch_15m(name, inst, START, END)

print("\nDone! Files:")
for f in sorted(DATA_DIR.glob("*_15m.csv")):
    sz = f.stat().st_size / 1024
    print(f"  {f.name} ({sz:.0f}KB)")
