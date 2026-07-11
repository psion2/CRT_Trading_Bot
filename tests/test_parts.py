"""
CRT Pattern Detector Test (Parts 1 + 2)

Fetches 4H data from Binance, simulates CRT/2C pattern detection,
and logs every boundary with pattern matches.

Usage:
    python tests/test_parts.py [--symbol BTC/USDT] [--limit 200]
"""

import ccxt
import argparse
from datetime import datetime

# ─── Config ────────────────────────────────────────────────────────────────
HTF_RESOLUTION = "4h"  # matches PineScript htfRes = "240"
ARRAY_MAX = 100  # matches PineScript while-loop pop limit

# ─── Fetch Data ────────────────────────────────────────────────────────────

def fetch_data(symbol: str, limit: int = 200):
    exchange = ccxt.binance({"enableRateLimit": True})
    since = exchange.parse8601("2026-05-01T00:00:00Z")

    # Fetch 4H candles
    htf_ohlcv = exchange.fetch_ohlcv(symbol, HTF_RESOLUTION, since=since, limit=limit)
    print(f"Fetched {len(htf_ohlcv)} {HTF_RESOLUTION} candles from Binance")

    # Convert to list of dicts for easier access
    htf_bars = []
    for ohlcv in htf_ohlcv:
        htf_bars.append({
            "time": ohlcv[0],
            "open": ohlcv[1],
            "high": ohlcv[2],
            "low": ohlcv[3],
            "close": ohlcv[4],
        })

    return htf_bars


# ─── Simulate Array Building ──────────────────────────────────────────────

def simulate_arrays(htf_bars):
    """Replicates PineScript array storage logic.

    PineScript:
        if isNew4H
            array.unshift(h4Opens,  htfO1)   -- htfO1 = open[1] (prev 4H candle)
            array.unshift(h4Highs,  htfH1)
            array.unshift(h4Lows,   htfL1)
            array.unshift(h4Closes, htfC1)
            while array.size > 100: array.pop(...)

    So at bar N (first bar with new 4H time), we push the *previous* 4H bar's OHLC.
    """

    h4_opens = []
    h4_highs = []
    h4_lows = []
    h4_closes = []

    log_entries = []

    for i in range(1, len(htf_bars)):
        prev = htf_bars[i - 1]
        curr = htf_bars[i]

        is_new = curr["time"] != prev["time"]

        if is_new:
            # Push the NOW-COMPLETED candle's data (PineScript: request.security with lookahead_off returns prev bar)
            h4_opens.insert(0, prev["open"])
            h4_highs.insert(0, prev["high"])
            h4_lows.insert(0, prev["low"])
            h4_closes.insert(0, prev["close"])

            # Trim
            while len(h4_opens) > ARRAY_MAX:
                h4_opens.pop()
                h4_highs.pop()
                h4_lows.pop()
                h4_closes.pop()

            # Log state
            ts = datetime.utcfromtimestamp(curr["time"] / 1000)
            entry = {
                "time": ts.strftime("%Y-%m-%d %H:%M"),
                "array_size": len(h4_opens),
                "idx0_open": h4_opens[0] if len(h4_opens) > 0 else None,
                "idx0_high": h4_highs[0] if len(h4_highs) > 0 else None,
                "idx0_low": h4_lows[0] if len(h4_lows) > 0 else None,
                "idx0_close": h4_closes[0] if len(h4_closes) > 0 else None,
                "idx0_dir": "BULL" if h4_closes[0] > h4_opens[0] else "BEAR" if len(h4_opens) > 0 else None,
                "idx1_high": h4_highs[1] if len(h4_highs) > 1 else None,
                "idx1_low": h4_lows[1] if len(h4_lows) > 1 else None,
                "idx1_open": h4_opens[1] if len(h4_opens) > 1 else None,
                "idx1_close": h4_closes[1] if len(h4_closes) > 1 else None,
                "idx2_high": h4_highs[2] if len(h4_highs) > 2 else None,
                "idx2_low": h4_lows[2] if len(h4_lows) > 2 else None,
                "idx2_open": h4_opens[2] if len(h4_opens) > 2 else None,
                "idx2_close": h4_closes[2] if len(h4_closes) > 2 else None,
            }
            # ─── Part 2: Pattern Detection ──────────────────────────────
            # Standard CRT 1-2-3 (need at least 3 completed bars)
            if len(h4_highs) >= 3:
                c1H = h4_highs[2]
                c1L = h4_lows[2]
                c2H = h4_highs[1]
                c2L = h4_lows[1]
                c2C = h4_closes[1]
                c3H = h4_highs[0]
                c3L = h4_lows[0]
                c3C = h4_closes[0]

                # C2 sweep
                c2SweepBear = c2H > c1H and c2C < c1H
                c2SweepBull = c2L < c1L and c2C > c1L

                # C3 confirm
                c3ConfBull = c3C > c2H and c2H < c1H and c3C > c1H
                c3ConfBear = c3C < c2L and c2L > c1L and c3C < c1L

                crtBull = c2SweepBull and c3ConfBull
                crtBear = c2SweepBear and c3ConfBear
                crtDir = 1 if crtBull else -1 if crtBear else 0
                crtEntry = c1L if crtBull else c1H if crtBear else None
                crtStop = c2L if crtBull else c2H if crtBear else None
            else:
                crtDir = 0
                crtEntry = crtStop = None

            # 2-Candle CRT (C1 = idx-1, C2 = idx-0 in array = our h[2]/h[1])
            if len(h4_highs) >= 2:
                _2c1H = h4_highs[1]
                _2c1L = h4_lows[1]
                _2c2H = h4_highs[0]
                _2c2L = h4_lows[0]
                _2c2C = h4_closes[0]
                _2cBull = _2c2L < _2c1L and _2c2C > _2c1H
                _2cBear = _2c2H > _2c1H and _2c2C < _2c1L
                _2cDir = 1 if _2cBull else -1 if _2cBear else 0
                _2cEntry = _2c2C if _2cDir != 0 else None
                _2cStop = _2c2L if _2cBull else _2c2H if _2cBear else None
            else:
                _2cDir = 0
                _2cEntry = _2cStop = None

            entry["crt_dir"] = crtDir
            entry["crt_entry"] = f"{crtEntry:.2f}" if crtEntry else "—"
            entry["crt_stop"] = f"{crtStop:.2f}" if crtStop else "—"
            entry["2c_dir"] = _2cDir
            entry["2c_entry"] = f"{_2cEntry:.2f}" if _2cEntry else "—"
            entry["2c_stop"] = f"{_2cStop:.2f}" if _2cStop else "—"

            log_entries.append(entry)

    return log_entries


# ─── Display ───────────────────────────────────────────────────────────────

def print_log(log_entries):
    print(f"\n{'='*166}")
    print(f"{'Time':20} {'Sz':4} | {'C3 O>C':20} {'C2 H/L':16} {'C1 H/L':16} | {'CRT':10} {'2C':10}")
    print(f"{'-'*166}")
    for e in log_entries:
        i0  = f"{e['idx0_open']:>9.2f}>{e['idx0_close']:<9.2f}"
        i1  = f"{e.get('idx1_high',0) or 0:>7.2f}/{e.get('idx1_low',0) or 0:<7.2f}"
        i2  = f"{e.get('idx2_high',0) or 0:>7.2f}/{e.get('idx2_low',0) or 0:<7.2f}"
        crt = f"{'BULL' if e['crt_dir']==1 else 'BEAR' if e['crt_dir']==-1 else '-'}"
        _2c = f"{'BULL' if e['2c_dir']==1 else 'BEAR' if e['2c_dir']==-1 else '-'}"
        print(f"{e['time']:20} {e['array_size']:4} | {i0:20} {i1:16} {i2:16} | {crt:10} {_2c:10}")


# ─── Main ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    htf_bars = fetch_data(args.symbol, args.limit)
    log = simulate_arrays(htf_bars)
    print_log(log)

    print(f"\nLogged {len(log)} 4H boundaries. Array building appears {'OK' if log else 'FAILED'}")
