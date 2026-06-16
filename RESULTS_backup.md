# CRT Trading Bot — Backtest Results

**Model:** `minimax-m2.5-free` via `opencode.ai/zen`  
**Date:** 2026-05-29  
**Capital:** $10,000 simulated, 2% risk per trade, SL=1.5%, TP=1.5x/2.0x  

---

## All Tests Conducted

### 1. EUR/USD Baseline (May 2024 – May 2026, 3116 candles, 4H)
**Config:** Base (KZ=OFF, M1=ON, KOD=ON, OTE=ON, BB=ON, C3=ON, MSS=ON)

| Trades | Win% | PnL | PF | Max DD | Sharpe |
|--------|------|-----|----|--------|--------|
| 36 | 22% | -$748 | 0.67 | 12.5% | -2.12 |

First test after initial implementation. All signals combined, no per-range guard.

---

### 2. Multi-Config Per Pair (Mar 2024 – May 2026, 4H)

#### BTC/USDT (4914 candles)
| Config | Trades | Win% | PnL | PF | DD% | Sharpe |
|--------|--------|------|-----|----|-----|--------|
| Base | 162 | 50.6% | **+$11,938** | 1.73 | 13.7% | 3.74 |
| KZ_ON | 66 | 51.5% | +$6,719 | 2.01 | 15.6% | 5.41 |
| C3_OFF | 188 | 36.7% | +$78 | 1.00 | 29.8% | 0.19 |
| M1_Only | 186 | 43.5% | +$2,460 | 1.15 | 22.0% | 1.12 |
| KOD_Only | 221 | 37.6% | +$4,075 | 1.26 | 25.5% | 1.38 |
| OTE_Only | 119 | 49.6% | +$5,695 | 1.47 | 14.9% | 2.85 |

#### ETH/USDT (4914 candles)
| Config | Trades | Win% | PnL | PF | DD% | Sharpe |
|--------|--------|------|-----|----|-----|--------|
| Base | 188 | 36.2% | +$5,041 | 1.27 | 13.6% | 1.48 |
| KZ_ON | 68 | 48.5% | +$9,050 | 1.93 | 11.7% | 3.77 |
| OTE_Only | 115 | 44.3% | +$13,941 | 2.34 | 12.4% | 3.73 |
| M1_Only | 209 | 44.0% | +$11,422 | 1.43 | 20.1% | 2.68 |
| KOD_Only | 254 | 44.1% | **+$23,241** | 1.78 | 11.4% | 3.44 |

#### SOL/USDT (4914 candles)
| Config | Trades | Win% | PnL | PF | DD% | Sharpe |
|--------|--------|------|-----|----|-----|--------|
| Base | 221 | 50.7% | +$43,155 | 1.78 | 12.9% | 4.72 |
| KZ_ON | 79 | 59.5% | +$13,232 | 2.34 | 9.7% | 5.92 |
| OTE_Only | 145 | 55.2% | +$28,545 | 2.34 | 13.2% | 5.34 |
| M1_Only | 263 | 54.0% | **+$48,673** | 1.76 | 13.2% | 4.91 |
| KOD_Only | 310 | 42.3% | +$18,269 | 1.38 | 18.0% | 2.72 |

#### EUR/USD (3116 candles)
| Config | Trades | Win% | PnL | PF | DD% | Sharpe |
|--------|--------|------|-----|----|-----|--------|
| Base | 19 | 26.3% | -$411 | 0.71 | 7.8% | -2.11 |
| KZ_ON | 12 | 33.3% | -$288 | 0.72 | 5.9% | -2.18 |
| OTE_Only | 17 | 23.5% | -$750 | 0.45 | 9.7% | -4.82 |
| M1_Only | 23 | 21.7% | **-$167** | 0.86 | 5.9% | -0.70 |
| KOD_Only | 19 | 15.8% | -$602 | 0.49 | 7.9% | -3.76 |

#### GBP/USD (3116 candles)
| Config | Trades | Win% | PnL | PF | DD% | Sharpe |
|--------|--------|------|-----|----|-----|--------|
| Base | 25 | 16.0% | -$612 | 0.56 | 6.1% | -2.97 |
| KZ_ON | 14 | 14.3% | -$713 | 0.35 | 8.7% | -6.21 |
| OTE_Only | 21 | 33.3% | **+$295** | 1.30 | 4.1% | 1.63 |
| M1_Only | 25 | 40.0% | -$84 | 0.95 | 6.1% | -0.19 |
| KOD_Only | 26 | 30.8% | -$497 | 0.75 | 8.2% | -1.80 |

#### XAU/USD (3116 candles)
| Config | Trades | Win% | PnL | PF | DD% | Sharpe |
|--------|--------|------|-----|----|-----|--------|
| Base | 74 | 31.1% | +$802 | 1.20 | 10.1% | 1.20 |
| KZ_ON | 22 | 36.4% | +$240 | 1.15 | 5.9% | 1.03 |
| OTE_Only | 50 | 40.0% | +$782 | 1.23 | 9.7% | 1.42 |
| M1_Only | 79 | 45.6% | **+$4,098** | 1.91 | 7.8% | 4.42 |
| KOD_Only | 83 | 37.3% | +$475 | 1.09 | 18.5% | 0.66 |

---

### 3. LTF Confirmation Test (BTC/USDT overlap, Mar 2024 – Aug 2025, 3125 candles 4H + 50,000 candles 15m)
| Config | LTF | Trades | Win% | PnL | PF | DD% |
|--------|-----|--------|------|-----|----|-----|
| Base | OFF | 100 | 51.0% | +$6,862 | 1.77 | 13.7% |
| Base | ON | 56 | 48.2% | +$1,904 | 1.30 | 11.6% |
| KZ_ON | OFF | 47 | 61.7% | +$8,946 | 4.94 | 2.1% |
| KZ_ON | ON | 26 | 73.1% | +$8,628 | 8.46 | 2.0% |
| OTE_Only | OFF | 74 | 50.0% | +$2,171 | 1.28 | 14.3% |
| OTE_Only | ON | 46 | **71.7%** | **+$10,209** | **5.36** | **4.0%** |

---

### 4. Performance Profiling
| Pair | Candles | Time/test | Candles/sec |
|------|---------|-----------|-------------|
| BTC/USDT | 4914 | ~43s | ~114 |
| ETH/USDT | 4914 | ~45s | ~109 |
| SOL/USDT | 4914 | ~37s | ~133 |
| EUR/USD | 3116 | ~23s | ~135 |
| GBP/USD | 3116 | ~23s | ~135 |
| XAU/USD | 3116 | ~22s | ~142 |

---

## Key Findings

### What Works
1. **CRT on crypto is highly profitable:** 10/10 configs on BTC/ETH/SOL are positive. SOL Base +431%, ETH KOD_Only +232%, BTC Base +119%.
2. **M1_Only is the most consistent winner:** Works on all 3 crypto pairs and gold. Simple, robust.
3. **KOD_Only is best on ETH** (+$23,241) but mediocre on others.
4. **OTE_Only + LTF confirmation** is a killer combo: $2,171→$10,209, WR 50%→71.7%, DD 14.3%→4.0%.
5. **Kill Zone filters aggressively:** reduces trades 55-70% but improves win rate/PF per trade.
6. **Candle 3 filter is essential:** turning it off drops WR from 50.6%→36.7%, DD doubles.

### What Doesn't Work
1. **EUR/USD:** Negative across all 5 configs. Best is M1_Only at -$167 (near breakeven).
2. **GBP/USD:** Only OTE_Only is barely positive (+$295). Others lose.
3. **Base + LTF:** LTF confirmation hurts Base config on BTC (trades halved, PnDrops 72%).

### Open Questions
1. **One signal vs multiple signals per CRT range** — see discussion below.
2. **Forex/metals LTF data** — only have 60 days of yfinance 15m, not enough for backtest. Need OANDA/Dukascopy source.

---

### 5. Per-Phase Signaling Results (Mar 2024 – May 2026, 4H)

**Change:** Replaced `has_signaled` (one signal per range) with per-phase flags (Model-1, Breaker, OTE, KOD each fire independently).

Each CRT range can now generate up to 4 signals. Two stop modes tested:
- **Independent:** Each trade keeps its own invalidation level as SL
- **TSQ Trail:** When a later TSQ phase fires for same range, ALL open positions from that range get their SL tightened to the new phase's invalidation level

#### BTC/USDT
| Config | Stop Mode | Trades | Win% | PnL | PF | DD% | Sharpe |
|--------|-----------|--------|------|-----|----|-----|--------|
| Base | independent | 1338 | 55.8% | $52,395 | 1.22 | 50.2% | 1.35 |
| Base | **tsq_trail** | **1321** | **55.0%** | **$74,649** | **1.26** | **43.2%** | **1.61** |
| OTE_Only | both | 324 | 56.5% | $6,286 | 1.18 | 25.2% | 1.46 |
| KZ_ON | independent | 399 | 54.4% | $3,299 | 1.09 | 39.9% | 0.77 |
| KZ_ON | **tsq_trail** | **396** | **54.3%** | **$4,462** | **1.13** | **34.5%** | **0.97** |

#### ETH/USDT
| Config | Stop Mode | Trades | Win% | PnL | PF | DD% | Sharpe |
|--------|-----------|--------|------|-----|----|-----|--------|
| Base | independent | 1354 | 55.5% | $48,195 | 1.14 | 51.1% | 1.29 |
| Base | **tsq_trail** | **1330** | **54.4%** | **$66,363** | **1.18** | **46.7%** | **1.53** |
| OTE_Only | both | 271 | 54.2% | $2,460 | 1.09 | 20.7% | 0.85 |
| KOD_Only | both | 770 | 53.8% | $9,493 | 1.09 | 34.2% | 0.91 |

#### SOL/USDT
| Config | Stop Mode | Trades | Win% | PnL | PF | DD% | Sharpe |
|--------|-----------|--------|------|-----|----|-----|--------|
| Base | independent | 1447 | 56.7% | $77,851 | 1.14 | 48.6% | 1.47 |
| Base | **tsq_trail** | **1423** | **55.2%** | **$108,200** | **1.17** | **41.5%** | **1.73** |
| OTE_Only | both | 328 | 53.0% | $1,672 | 1.05 | 23.5% | 0.56 |
| M1_Only | both | 629 | 55.6% | $11,597 | 1.12 | 42.5% | 1.22 |

#### XAU/USD
| Config | Stop Mode | Trades | Win% | PnL | PF | DD% | Sharpe |
|--------|-----------|--------|------|-----|----|-----|--------|
| M1_Only | both | 347 | 61.7% | **$24,287** | 1.47 | 21.0% | **3.37** |

---

### 6. Stop Mode Comparison Summary

**TSQ Trail beats Independent** in every multi-phase config (Base, KZ_ON):
- BTC Base: +$22,254 (42%) more PnL, -7% DD
- ETH Base: +$18,168 (38%) more PnL, -4.4% DD
- SOL Base: +$30,349 (39%) more PnL, -7.1% DD

**Single-phase configs (OTE_Only, KOD_Only, M1_Only)** are identical in both modes — they only fire one signal per range so there are no later phases to trail from.

---

### 7. Key Trade-off: Conservative vs Aggressive

The `has_signaled` approach (one signal per range) and the per-phase approach represent fundamentally different strategies:

| Approach | BTC Base Trades | BTC Base PnL | BTC Base DD% | BTC Base Sharpe |
|----------|----------------|-------------|-------------|-----------------|
| **Conservative** (has_signaled) | 162 | $11,938 | 13.7% | **3.74** |
| **Aggressive** (per-phase, tsq_trail) | 1321 | **$74,649** | 43.2% | 1.61 |

**Conservative:** Higher risk-adjusted returns, lower absolute returns, lower drawdown, fewer trades (better for smaller accounts)
**Aggressive:** Higher absolute returns, 3x higher drawdown, more trades (better for larger/compound accounts)

---

## Per-Pair Recommended Configs

| Pair | Suggested Config | Stop Mode | PnL | Win% | DD% | Sharpe | Notes |
|------|-----------------|-----------|-----|------|-----|--------|-------|
| BTC/USDT | Base | conservative (has_signaled) | $11,938 | 50.6% | 13.7% | 3.74 | Best risk-adjusted |
| BTC/USDT | Base | aggressive (per-phase+trail) | $74,649 | 55.0% | 43.2% | 1.61 | Best absolute return |
| ETH/USDT | KOD_Only | either | $23,241 | 44.1% | 11.4% | 3.44 | Best risk-adjusted crypto |
| ETH/USDT | Base+trail | aggressive | $66,363 | 54.4% | 46.7% | 1.53 | Best absolute return |
| SOL/USDT | Base+trail | aggressive | $108,200 | 55.2% | 41.5% | 1.73 | Best overall absolute |
| SOL/USDT | M1_Only | either | $48,673 | 54.0% | 13.2% | 4.72 | Best risk-adjusted overall |
| EUR/USD | M1_Only (needs tuning) | either | -$167 | 21.7% | 5.9% | -0.70 | Near breakeven |
| GBP/USD | OTE_Only | either | $295 | 33.3% | 4.1% | 1.63 | Barely positive |
| XAU/USD | M1_Only | either | $24,287 | 61.7% | 21.0% | 3.37 | Excellent risk-adjusted |
