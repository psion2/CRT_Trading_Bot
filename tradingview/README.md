# CRT Pattern Detector — TradingView Indicator (MTF)

Multi-timeframe Candle Range Theory indicator. Detects 4H patterns (CRT, 2-Candle CRT, Inside-Bar CRT) and overlays entry triggers on the 15M chart.

## How to Install

1. Open TradingView → **Pine Editor** (bottom panel)
2. Copy entire contents of `tradingview/crt_indicator.pine`
3. Paste → **Save** → **Add to Chart**
4. Set chart timeframe to **15M** (best performance)

## Legend — Every Symbol Explained

### 4H Pattern Markers (appear at new 4H candle open)

| Symbol | Shape | Color | Label | Meaning |
|--------|-------|-------|-------|---------|
| ↑↓ | Arrow up/down | Blue | `CRT` | Standard 1-2-3 CRT: C1=range, C2=sweep, C3=expansion |
| ↑↓🚀 | Arrow up/down | Fuchsia | `2C` | 2-Candle CRT: C1=range, C2=sweeps + distributes in one candle |
| ↑↓ | Arrow up/down | Aqua | `IB` | Inside-Bar CRT: range candle + N inside candles + breakout |

### 15M Pattern Markers (appear per-bar on 15M)

| Symbol | Shape | Colors | Label | Meaning |
|--------|-------|--------|-------|---------|
| ▲ | Triangle down | Orange | `Swing H` | 5-bar pivot high |
| ▲ | Triangle up | Orange | `Swing L` | 5-bar pivot low |
| ♦ | Diamond | Green / Red | `TS Bull` / `TS Bear` | Price sweeps prior swing low/high then closes back above/below |
| ■ | Square | Lime / Maroon | `M1 Bull` / `M1 Bear` | Thick candle sweeps swing, next candle confirms direction |
| ✚ | Cross | Teal / Purple | `Brk Bull` / `Brk Bear` | Failed M1 — price reverses back through the M1 candle's range |
| ✕ | X | Yellow | `KOD Bull` / `KOD Bear` | "Kiss of Death" — Turtle Soup within OTE zone after recent swing |

### Entry Triggers (15M confirmation of 4H pattern)

| Symbol | Label | Color | Meaning |
|--------|-------|-------|---------|
| ⚡ | `⚡ ENTRY CRT LONG` | Yellow | 15M confirmed the 4H level — M1 in same direction OR price crossed entry level |

### 4H Range Boxes

| Symbol | Color | Meaning |
|--------|-------|---------|
| ▭ | Semi-transparent blue box labelled `C1` | Shows C1's high-low range spanning its 4-hour window |

### 4H Trade Levels (Entry/SL/TP)

Drawn when a 4H pattern is detected AND `Show Entry/SL/TP` is ON:

| Symbol | Label | Color | Meaning |
|--------|-------|-------|---------|
| ┅┅ | Dashed line | Lime / Red | Direction line: `CRT LONG` / `2C SHORT` |
| ┅┅ | Dashed line + `ENTRY: 52341.5` | Lg = direction, Sm = faded | Limit entry level (C1 extreme / C2 close / range extreme) |
| ┅┅ | Dashed line + `SL: 52150.0` | Red (faded) | Stop loss (C2 extreme / C2 sweep / C0 extreme) |
| ╌╌ | Dotted line + `TP1: 52780.0` | Green (faded) | 1st take-profit at 1.5× risk |
| ╌╌ | Dotted line + `TP2: 53000.0` | Lime (faded) | 2nd take-profit at 2.0× risk |

### 15M Trade Levels (Model-1 only)

Same Entry/SL/TP labels as above but for the 15M Model-1 pattern (4H-independent). SL uses ATR-based offset.

### Filtering Overlays

| Symbol | Element | Meaning |
|--------|---------|---------|
| 🟦 | Blue tint background | Within Kill Zone (London 2-5AM or NY 7-10AM chart time) |
| ⬜ | Gray tint background | Outside Kill Zone (only when KZ filter is enabled) |
| 🟢 | Green dashed line at top | DLP direction is bullish (last sweep was bullish) |
| 🔴 | Red dashed line at top | DLP direction is bearish (last sweep was bearish) |
| ⛔ | `⛔ OUTSIDE KZ` label | Signal suppressed by Kill Zone filter (warn ON) |
| ⚠️ | `⚠ DLP FILTERED` label | Signal suppressed by DLP filter (direction conflict) |
| ⛔ | `⛔ DAY FILTERED (thu_fri)` label | Signal suppressed by Day Filter |
| 🟦 | Aqua box labelled `OTE` | Fibonacci 60-75% retracement zone between last two swings |

### Info Table (bottom-right corner)

| Row | Symbol | Content | Meaning |
|-----|--------|---------|---------|
| 1 | ℹ️ | `CRT MTF v1` | Indicator name |
| 2 | 🔄 | `240→15` | HTF resolution → chart timeframe |
| 3 | 🎯 | `DLP: BULL` (if enabled) | Current draw direction |
| 4 | 🕐 | `IN KZ` / `OUT KZ` (if enabled) | Whether inside kill zone |
| 5 | 💹 | `CRT @52341.5` (if active) | Active 4H signal type + entry price |

### Entry/SL Rules by Pattern

| Pattern | Entry | Stop Loss |
|---------|-------|-----------|
| **CRT 3-Candle** (4H) | C1's extreme (low for long, high for short) | C2's extreme (low for long, high for short) |
| **2-Candle CRT** (4H) | C2's close (distribution level) | C2's sweep extreme (C2 low for long, C2 high for short) |
| **Inside-Bar CRT** (4H) | Range candle's opposite extreme (range low for long, range high for short) | Breakout candle's extreme (C0 low for long, C0 high for short) |
| **Model-1** (15M) | Previous candle's extreme (swept swing level) | ATR-based offset (0.5× ATR) |
| **Breaker** (15M) | Previous M1 candle's body extreme | ATR-based offset (0.5× ATR) |
| **15M Entry Trigger** (4H→15M) | 4H pattern's entry level (C1 extreme / C2 close / range extreme) | 4H pattern's SL level |

## Filtering Features (All OFF by default)

### Kill Zones
- Enable → blocks alerts outside London (2-5AM) / NY (7-10AM) chart-time hours
- Warn → shows `⛔ OUTSIDE KZ` label for suppressed signals
- Shade → blue background in KZ, gray outside

### Draw Liquidity Priority
- After any TS sweep, sets a directional bias (bullish/bearish)
- Suppresses labels + alerts for M1/Breaker signals going AGAINST the draw direction
- Shows `⚠ DLP FILTERED` label + direction line at chart top
- Clears when entry trigger fires

### Day Filter
- `thu_fri`: only Thursday/Friday (highest probability per RULES.md)
- `mon_fri`: weekdays only (blocks weekends)
- Suppressed signals show `⛔ DAY FILTERED` label

## Alerts (Free Plan)

The indicator fires 1 alert per bar when ANY pattern is detected.
Filters (KZ / DLP / Day) also apply to alerts.

TradingView free plan allows **1 active alert**. To set it up:

1. Right-click chart → **Add Alert**
2. Condition: select **"CRT Det MTF"** → any of the patterns
3. Choose notification method (email/push)

Alert messages include all detected patterns:
```
CRT MTF: CRT [CRT BULL] ⚡ENTRY | M1 BULL | KOD BULL
```

## Configurable Parameters

| Group | Parameter | Default | Options |
|-------|-----------|---------|---------|
| Core | Swing Length | 5 | 2–20 |
| Core | Min Model-1 Body Ratio | 1.5 | 0.5– |
| Core | OTE Fib Low | 0.60 | 0.0–1.0 |
| Core | OTE Fib High | 0.75 | 0.0–1.0 |
| Core | HTF Resolution | 240 | 60 / 120 / 240 / 480 / D |
| Display | Show 4H CRT Patterns | ✓ | Toggle per pattern |
| Display | Show 15M Turtle Soup | ✓ | Toggle per pattern |
| Display | Show 15M Model-1 | ✓ | Toggle per pattern |
| Display | Show 15M Breaker | ✓ | Toggle per pattern |
| Display | Show OTE Zones | ✓ | Toggle per pattern |
| Display | Show KOD | ✓ | Toggle per pattern |
| Display | Show Entry/SL/TP | ✓ | On/Off |
| Display | Show 4H Range Boxes | ✓ | On/Off |
| Display | Alert on New Signal | ✓ | On/Off |
| Display | Show 15M Entry Triggers | ✓ | On/Off |
| Display | OTE Box Lookback | 30 | 10–100 |
| Kill Zones | Enable Filter | Off | On/Off |
| Kill Zones | Warn on Outside-KZ | ✓ | On/Off |
| Kill Zones | Shade Hours | ✓ | On/Off |
| Draw Liquidity | Enable Priority | Off | On/Off |
| Day Filter | Day Filter | any | any / thu_fri / mon_fri |
| Extra CRT | Show 2-Candle CRT | ✓ | On/Off |
| Extra CRT | Show Inside-Bar CRT | ✓ | On/Off |
| Extra CRT | Min Inside-Bar Candles | 3 | 2–20 |

## Timeframes

- **Chart**: 15M (primary — shows 15M patterns + 4H overlays + entry triggers)
- **HTF Resolution**: 240 (4H) — configurable to 60/120/480/D
- Works on any timeframe but 15M is tuned for the entry trigger logic

## MTF Workflow

1. 4H candle closes → arrays store its OHLC
2. Pattern detection runs on completed 4H candles (1-2-3 CRT, 2-candle, inside-bar)
3. If a pattern is found → `activeHTFSignal` stores its direction + entry + SL for 4 hours
4. On each 15M bar, two trigger checks run:
   - **M1 Confirmation**: 15M Model-1 fires in the same direction as the 4H signal
   - **Price Crossing**: 15M close crosses the 4H entry level
5. First trigger to fire creates a yellow `⚡ ENTRY` label (once per signal)
6. Signal expires after 4 hours (16 × 15M bars) or when the next 4H candle produces a new signal

## Limitations vs Python Bot

This PineScript detects patterns using basic pivot/swing logic. It's a **visual aid** for manual trading. The Python bot in this repo has more sophisticated detection with dynamic swing analysis and multi-phase TSQ sequencing. Use this indicator to:

- Verify signals before the bot enters
- Spot CRT patterns at a glance
- Practice manual CRT trading
- See which patterns are being filtered (KZ, DLP, Day)
- Identify 4H levels and wait for 15M confirmation

## Example Chart Setup

- Set chart to **15M** BTC/USDT
- Add indicator with default settings
- Blue C1 boxes appear every 4 hours showing range context
- Blue/fuchsia/aqua arrows mark 4H pattern types
- Orange triangles (swings) → diamonds (TS) → squares (M1) → crosses (BRK) → X (KOD)
- When 15M confirms a 4H level: yellow `⚡ ENTRY` label appears
- Entry/SL/TP dashed lines with price labels show trade levels
- Enable KZ shading to see high-probability windows
- Turn on DLP to avoid counter-trend setups
