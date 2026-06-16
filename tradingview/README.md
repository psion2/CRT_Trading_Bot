# CRT Pattern Detector — TradingView Indicator

Detects CRT patterns (Candle Range Theory) directly on TradingView charts.

## How to Install

1. Open TradingView → **Pine Editor** (bottom panel)
2. Copy entire contents of `tradingview/crt_indicator.pine`
3. Paste → **Save** → **Add to Chart**

## What It Shows

| Pattern | Marker | Color |
|---------|--------|-------|
| **Swing High/Low** | Triangle | Orange |
| **CRT Range** (1-2-3 candles) | Arrow | Blue |
| **Turtle Soup** (sweep + reversal) | Diamond | Green/Red |
| **Model-1** (thick sweep + close) | Square | Lime/Maroon |
| **Breaker Block** | Cross | Teal/Purple |
| **KOD** (final sweep) | X | Yellow |
| **OTE Zone** (60-75% fib) | Box | Aqua |
| **Entry/SL/TP** | Lines | Dashed |

## Alerts (Free Plan)

The indicator fires 1 alert per bar when ANY pattern is detected. TradingView free plan allows **1 active alert**. To set it up:

1. Right-click chart → **Add Alert**
2. Condition: select **"CRT Detector"** → any of the patterns
3. Choose notification method (email/push)

## Timeframes

Works best on **4H** (primary) and **1H/15m** (for detailed TSQ view).

## Limitations vs Python Bot

This PineScript detects patterns using basic pivot/swing logic. It's a **visual aid** for manual trading. The Python bot in this repo has more sophisticated detection with dynamic swing analysis and multi-phase TSQ sequencing. Use this indicator to:

- Verify signals before the bot enters
- Spot CRT patterns at a glance
- Practice manual CRT trading

## Configurable Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Swing Length | 5 | Bars for pivot detection |
| Min Model-1 Body Ratio | 1.5 | Minimum body:wax ratio for Model-1 |
| OTE Fib Low | 0.60 | Lower Fibonacci level for OTE |
| OTE Fib High | 0.75 | Upper Fibonacci level for OTE |
| Show/Hide patterns | ✓ | Toggle each pattern type |

## Example Chart Setup

- Add indicator to a **4H BTC/USDT** chart
- Look for orange triangles (swings) → blue arrows (CRT) → diamond (turtle soup) → entry lines
- Cross-check with bot signals from the dashboard
