# CRT Trading Bot - Rules Documentation

> This file documents all trading rules extracted from CRT sources.
> Source: MadoCRT, Romeotpt, SpeculatorFL

---

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [CRT Types](#crt-types)
3. [TSQ Sequence](#tsq-sequence-turtle-soup--crt-sequence)
4. [Pattern Rules](#pattern-rules)
5. [Model-1 Entry System](#model-1-entry-system)
6. [Timeframe Alignment](#timeframe-alignment)
7. [Multi-Timeframe Framework](#multi-timeframe-framework)
8. [Kill Zones](#kill-zones)
9. [Entry/Exit Rules](#entryexit-rules)
10. [Key Level Types](#key-level-types)
11. [Parameters](#parameters)
12. [Change Log](#change-log)

---

## Core Concepts

### What is CRT (Candle Range Theory)?
- Every candle = **time-based range** with Open, High, Low, Close
- Three elements: **Liquidity + Time + Price**
- **CRT High = Buyside Liquidity**
- **CRT Low = Sellside Liquidity**
- Price moves from liquidity to liquidity

### Key Principle
- **Range Break (True)**: Price breaks above CRT High or below CRT Low and continues
- **Range Break (False/Turtle Soup)**: Price sweeps one side, then reverses to opposite side

---

## CRT Types

### 1. Three Candle CRT (Core Model)
| Candle | Phase | Description |
|--------|-------|-------------|
| Candle 1 | Accumulation/Range | Creates the range (high = CRT High, low = CRT Low) |
| Candle 2 | Manipulation/Purge | Sweeps liquidity, tests key level, closes back inside range |
| Candle 3 | Distribution/Expansion | Price expands to opposite side of range |

**Example (4H):** 1:00 candle (range) → 5:00 candle (manipulation) → 9:00 candle (distribution)

### 2. Two Candle CRT
- Candle 1 creates the range
- Candle 2 does **both jobs**: purge AND distribute in same candle
- Often appears during high volatility/news events

### 3. Multiple Candle CRT
#### Inside Bar CRT
- Candle 1 creates the range
- Multiple candles remain trapped inside
- Wait for purge of one side → then expansion follows

#### Outside Bar CRT
- Candle 1 creates the range
- Candle 2 purges high or low
- Multiple candles distribute toward opposite side

---

## TSQ Sequence (Turtle Soup + CRT Sequence)

> **Source:** MadoCRT EP 4 - Complete TSQ Sequence

### What is TSQ?
- TSQ maps the **complete journey of price inside a CRT** after purge
- Not every setup shows all phases — sometimes 2, sometimes all 6
- TSQ always **starts and ends with turtle soup**

### TSQ Phases (in order)

| Phase | Name | Description |
|-------|------|-------------|
| 1 | **Turtle Soup** | Liquidity purge (trap) - the starting point |
| 2 | **Model-1** | Confirmation after turtle soup |
| 3 | **Breaker Block** | Structure break, old candle becomes breaker (last candle before displacement) |
| 4 | **OTE** | Optimal Trade Entry - 60-75% Fibonacci retracement zone |
| 5 | **Kiss of Death (KOD)** | Final turtle soup before reaching draw on liquidity |

### Phase Details

#### Phase 1: Turtle Soup (TSQ Starts Here)
- Same as standard turtle soup (liquidity purge)
- **TSQ starts with turtle soup and ends with turtle soup**
- Bulls: Purge CRT low → reverse up
- Bears: Purge CRT high → reverse down

#### Phase 2: Model-1
- Confirmation of turtle soup validity
- Wait for close above/below the purge candle
- This candle becomes Model-1

#### Phase 3: Breaker Block
- After Model-1 displacement, market breaks internal structure
- Returns to retest the **last bearish candle** (bullish case) or **last bullish candle** (bearish case)
- That retest candle becomes the **breaker block**
- Entry opportunity at breaker retest

#### Phase 4: OTE (Optimal Trade Entry)
- **Fibonacci 60-75% retracement zone** of the displacement move
- Market pulls back before continuing
- **Requirements for valid OTE trade:**
  1. Clear HTF bias
  2. Liquidity was purged before retracement
  3. Valid Model forming inside OTE zone (CRT, turtle soup, micro Model-1)
- Stop loss: Below protected swing low (buys) / above protected swing high (sells)
- Target: Next liquidity pool or CRT high/low

#### Phase 5: Kiss of Death (KOD)
- **Final turtle soup before market reaches draw on liquidity**
- Signals market is preparing to deliver into target
- The most important phase (according to MadoCRT)
- Also known as "redistribution" in ICT

### Timeframe Alignment for TSQ

| CRT Timeframe | TSQ Observation |
|---------------|-----------------|
| Weekly | 4H |
| Daily | 1H |
| 4H | 15min |
| 1H | 5min |

### Where to Apply TSQ
- Inside CRT range
- From key level to draw on liquidity
- From CRT high to CRT low (and vice versa)
- From OHL(C) structure as reference points

### TSQ Flexibility
- **Strong trending market:** May only show turtle soup + Model-1
- **Complex/slow market:** May show all phases (breaker → OTE → KOD)
- **Goal:** Recognize what's actually there, don't force full sequence

---

## OHLC/OLHC Candle Logic with TSQ

> **Source:** MadoCRT EP 5 - TSQ Phases Using OHLC & OLHC

### Candle Structures
| Structure | Candle Type | TSQ Direction |
|-----------|------------|--------------|
| Open → Low → High → Close | Bullish | Uptrend phases |
| Open → High → Low → Close | Bearish | Downtrend phases |

### OHLC TSQ Sequence (Bullish - OLC)
1. **Open** → Price opens
2. **Liquidity generation** → Turtle soup on short-term low
3. **Expansion** → Aggressive move up (no consolidation = real displacement)
4. **Close above short-term high** → Activates breaker block phase
5. **Return to breaker area** → Breaker block phase
6. **Deep retracement** → OT phase (may act like KOD)
7. **Final turtle soup** → Completes the TSQ cycle

### OLHC TSQ Sequence (Bearish - OHC)
- Same logic, **all phases flipped**
- Bearish turtle soup → expansion down → breaker block below → etc.

### Confirmation Rule
> **"Closes tell the truth. Wicks lie. Closes confirm."**

- Close above = confirm higher prices
- Close below = confirm lower prices
- Wicks can be deceptive — always wait for candle close

### HTF Wick = LTF Expansion
- When HTF hits draw on liquidity and does turtle soup (wick)
- LTF will have at least one short-term expansion move
- One HTF wick can create **multiple LTF CRT opportunities**

### Breaker + OTE Combination
> **When breaker block and OTE combine at the same zone = highest probability**

- Breaker + OTE = strong continuation signal
- Often the strongest phase of TSQ

### Time-Based TSQ on Monthly Candle
| Week | Expected Phase |
|------|----------------|
| Week 1 | Range / Liquidity buildup |
| Week 2 | Manipulation / Turtle soup + Expansion |
| Week 3 | OTE or Kiss of Death |
| Week 4 | Final turtle soup (completes monthly candle) |

### Professional Trading Flow
1. **HTF gives direction** (bias, order flow)
2. **LTF gives execution** (CRT setup, Model-1)
3. Drop to LTF when HTF activates a phase
4. Wait for CRT → Position → Cleaner entry, smaller stop, higher reward

---

## Turtle Soup (RomeoTPT)

> **Source:** RomeoTPT - What is Turtle Soup?

### Definition
- Turtle Soup = **False breakout** or **false breakdown**
- Market maker deliberately pushes price **above old high** or **below old low**
- Goal: Fill large orders to move price in intended direction

### Why Turtle Soup Exists
- 90%+ of retail traders have **trend-following systems**
- Retail places buy stops above old highs, sell stops below old lows
- Market maker uses this liquidity to move price in opposite direction
- **90% of traders lose** because they chase breakouts

### Bearish Turtle Soup
```
Old High → Decline → Buy stops above old high → Short stops above old high
↓
Price stabs above old high
↓
Stops knocked out, new longs trapped
↓
Price DUMPS
```

### Bullish Turtle Soup
```
Old Low → Rally → Sell stops below old low → Long stops below old low
↓
Price stabs below old low
↓
Stops knocked out, new shorts trapped
↓
Price RALLIES
```

### Turtle Soup Mechanics
| Element | Description |
|---------|-------------|
| Old High/Low | Previous swing high/low |
| Buy Stops | Above old high (from breakout traders) |
| Sell Stops | Below old low (from breakdown traders) |
| Short Stops | Above old high (from failed short) |
| Long Stops | Below old low (from failed long) |

### Key Insight
> **"Price only moves in a certain direction after making sure everyone who wanted that direction is knocked out."**

### Rules for Trading Turtle Soup (RomeoTPT)
1. **Buy Low, Sell High** — Trade the reversal, not the breakout
2. **Understand market profiles** — (details in next videos)
3. **Understand different entry models** — (details in upcoming videos)
4. **Always monitor HTF price action** — Critical for context
5. **Always manage risk** — Even 90% win rate fails without risk management

### Progression for Mastery
| Step | Action |
|------|--------|
| Step 1 | Learn the concept |
| Step 2 | Watch it happen 100-1000 times live |
| Step 3 | Trade it |

### Entry Timing
- Beginners: Wait for confirmation (after the wick)
- Experienced: Can enter into the wick itself
- Goal: Eventually enter during the turtle soup wick

---

## CRT (RomeoTPT)

> **Source:** RomeoTPT - What is CRT? Why do all other trading strategies suck?

### What is CRT?
- **CRT = Candle Range Theory**
- Every candle = a **range**
- Every range can either be:
  1. **Broken out of** (continuation)
  2. **Turtle souped** (reversal)
- There is **no third option**

### Power of Three (Timeframe Alignment)
> **CRT fractal nature: Whatever happens on HTF happens on LTF at different speed**

| Higher Timeframe | Lower Timeframe |
|------------------|-----------------|
| Monthly | 4H |
| Weekly | 1H |
| Daily | 15min |
| 4H | 5min |

### The Base Premise (Core Pattern)
```
OPEN + KEY LEVEL + TURTLE SOUP + MOVE
```

| Direction | Pattern |
|-----------|---------|
| **Bearish** | Open + Key Level + Turtle Soup + Decline |
| **Bullish** | Open + Key Level + Turtle Soup + Rally |

**Write this down. This is everything.**

### Candle 1-2-3 Sequence
| Candle | Phase | Description |
|--------|-------|-------------|
| Candle 1 | **Accumulation** | Range forms |
| Candle 2 | **Manipulation** | Turtle soup / liquidity sweep |
| Candle 3 | **Distribution** | Target hit |

> **"Sell above the open of candle 3"** (for bearish)
> **"Buy below the open of candle 3"** (for bullish)

### 50% Rule (Key Target)
> **"Any candle that gets turtle souped → expect to trade to at least the 50% of the range"**

- **Always partial at 50%**
- Full target: Opposite end of the range
- 50% is the **minimum guaranteed target**

### Weekly Timeline (Time Theory)
| Week | Phase |
|------|-------|
| Week 1 | Accumulation (Candle 1) |
| Week 2 | Manipulation (Candle 2) |
| Week 3+ | Distribution (Candle 3) |

### Bias Rules (Close vs Wick)
| Signal | Expectation |
|--------|-------------|
| Close **above** previous candle | Higher prices next candle |
| Close **below** previous candle | Lower prices next candle |
| Wick **above** previous candle | Lower prices next candle |
| Wick **below** previous candle | Higher prices next candle |

> **"Close above = higher, Close below = lower, Wicks lie, closes confirm"**

### Entry Sequence (Three Models)
| Entry | Model | Description |
|-------|-------|-------------|
| Entry 1 | **Turtle Soup** | Most advanced, enter on the wick |
| Entry 2 | **Order Block / Model-1** | Wait for close above/below the sweep candle |
| Entry 3 | **Breaker / MSS** | Market structure shift confirmation |

### Model-1 Details (RomeoTPT Version)
- Wait for candle that **dug into old high/low**
- Wait for **close above** (bullish) or **close below** (bearish) that candle
- The candle that caused the move = Model-1
- **Ignore wicks, look at bodies**

### Sell Above / Buy Below Open Rule
- **Bearish**: Sell above the Monday midnight open
- **Bullish**: Buy below the Monday midnight open
- All breakers, order blocks, turtle soups happen **above or below the open**
- **Above = Bearish, Below = Bullish**

### Market Movement Pattern
```
RANGE → TREND → RANGE → TREND (always)
```

- Range = generation of interest (buy + sell side liquidity)
- First breakout of range = usually fake (turtle soup)
- Turtle soup → transition from range to trend

### Key Principles
1. **Time is more important than price**
2. **Every high and low is timed**
3. **Don't force turtle soup** — if it's not there, wait
4. **Target 50% first**, then opposite end of range
5. **Ask: Who's getting screwed?** (Retail buys above highs, sells below lows)

### Success Metrics
- **Daily**: 4 turtle soup setups per month = better than 90% of traders
- **4H**: 1-2 per week = better than most traders
- **Candle 3 = fastest trade** (most velocity)

### Daily/Weekly Open Rule
- **Daily candle open**: Monday midnight (NY time)
- **Weekly candle open**: Sunday 5:00 PM (NY time)
- Algorithm functions on NY time

### Market Maker Logic
- Market makers use retail liquidity to move price
- Retail buys above highs → market makers dump
- Retail sells below lows → market makers pump
- **"Who's getting stopped out?"** = always ask this question

---

## Model-1 (CRT Secrets EP 1)

> **Source:** RomeoTPT - CRT Secrets EP 1: One CRT model for life

### What is Model-1?
- **One specific candle** that stabbed into old high/low
- Wait for **close** below/above that candle → trigger
- **Highest risk-to-reward model** that exists

### Model-1 Rules

#### Bearish Model-1
```
Old High → Thick Up-Close Candle stabs above it → Close below = SHORT
Entry: Below the model-1 candle
Stop Loss: Above the model-1 candle
Target: Lows one by one
```

#### Bullish Model-1
```
Old Low → Thick Down-Close Candle stabs below it → Close above = LONG
Entry: Above the model-1 candle
Stop Loss: Below the model-1 candle
Target: Highs one by one
```

### Key Requirements
| Requirement | Why It Matters |
|-------------|----------------|
| **THICK candle** | Strong manipulation = high probability |
| **Close confirmation** | Never enter on wick alone |
| **Specific candle** | One candle, not a zone or range |

### Common Mistake
> **"You don't pick the thick candles. You're not selective. You take any random trade and lose."**

- Only trade **thick** up-close or down-close candles
- Ignore flimsy/small body candles
- **Be selective** — best trades present themselves to you

### FVG Enhancement
| With FVG | Without FVG |
|----------|-------------|
| **Higher probability** | Standard probability |

- Model-1 + FVG = highest probability setup
- Always prefer trades that come with an FVG

### Multi-Timeframe Alignment (CRT Model-1)
| Higher Timeframe | Model-1 Timeframe |
|------------------|-------------------|
| Monthly | Daily |
| Weekly | 4H |
| Daily | 1H |
| 4H | 15min |

### Time Theory (CRT Model-1 Specific)

#### Weekly Time Formation
| Day | Behavior |
|-----|----------|
| **Monday** | Fake high created (trap) |
| **Tuesday** | **Real high of the week forms** |
| **Thursday/Friday** | Opposite end of range kept |

#### The Magic Formula
> **"Time and price meet = magic. Thursday/Friday + Model-1 = bet the house"**

#### Weekly High/Low Timing
- **Weekly open**: Monday midnight (NY time)
- **Weekly close**: Friday 5:00 PM (NY time)
- **High forms early week** (Mon-Tue)
- **Low/Opposite end forms late week** (Thu-Fri)

### Time Principle
> **"If the time is right, the pattern will work. If the time is wrong, the pattern will fail."**

- Time is **more important than price**
- Align trades with correct time windows
- Thursday/Friday Model-1 = highest conviction

### System vs Human Error
| Factor | Truth |
|--------|-------|
| System | **Perfect** (market making mechanism) |
| Human | Makes mistakes, causes losses |

> **"System is never wrong. Most successful traders blame themselves for losses, never the system."**

### Selection Criteria for Model-1
1. **Old high/low present**
2. **Thick candle** stabs into it
3. **Close confirmation** (not wick)
4. **Time alignment** (ideally Thu/Fri or kill zones)
5. **FVG present** (optional but preferred)

### Entry/Stop/Target Summary
| Type | Bearish | Bullish |
|------|---------|---------|
| **Trigger** | Close below thick up-candle | Close above thick down-candle |
| **Entry** | Below model-1 candle | Above model-1 candle |
| **Stop Loss** | Above model-1 candle | Below model-1 candle |
| **Target** | Lows one by one | Highs one by one |

---

## Pattern Rules

---

## Core Concepts

### What is CRT (Candle Range Theory)?
- Every candle = **time-based range** with Open, High, Low, Close
- Three elements: **Liquidity + Time + Price**
- **CRT High = Buyside Liquidity**
- **CRT Low = Sellside Liquidity**
- Price moves from liquidity to liquidity

### Key Principle
- **Range Break (True)**: Price breaks above CRT High or below CRT Low and continues
- **Range Break (False/Turtle Soup)**: Price sweeps one side, then reverses to opposite side

---

## CRT Types

### 1. Three Candle CRT (Core Model)
| Candle | Phase | Description |
|--------|-------|-------------|
| Candle 1 | Accumulation/Range | Creates the range (high = CRT High, low = CRT Low) |
| Candle 2 | Manipulation/Purge | Sweeps liquidity, tests key level, closes back inside range |
| Candle 3 | Distribution/Expansion | Price expands to opposite side of range |

**Example (4H):** 1:00 candle (range) → 5:00 candle (manipulation) → 9:00 candle (distribution)

### 2. Two Candle CRT
- Candle 1 creates the range
- Candle 2 does **both jobs**: purge AND distribute in same candle
- Often appears during high volatility/news events

### 3. Multiple Candle CRT
#### Inside Bar CRT
- Candle 1 creates the range
- Multiple candles remain trapped inside
- Wait for purge of one side → then expansion follows

#### Outside Bar CRT
- Candle 1 creates the range
- Candle 2 purges high or low
- Multiple candles distribute toward opposite side

---

## TSQ Sequence (Turtle Soup + CRT Sequence)

> **Source:** MadoCRT EP 4 - Complete TSQ Sequence

### What is TSQ?
- TSQ maps the **complete journey of price inside a CRT** after purge
- Not every setup shows all phases — sometimes 2, sometimes all 6
- TSQ always **starts and ends with turtle soup**

### TSQ Phases (in order)

| Phase | Name | Description |
|-------|------|-------------|
| 1 | **Turtle Soup** | Liquidity purge (trap) - the starting point |
| 2 | **Model-1** | Confirmation after turtle soup |
| 3 | **Breaker Block** | Structure break, old candle becomes breaker (last candle before displacement) |
| 4 | **OTE** | Optimal Trade Entry - 60-75% Fibonacci retracement zone |
| 5 | **Kiss of Death (KOD)** | Final turtle soup before reaching draw on liquidity |

### Phase Details

#### Phase 1: Turtle Soup (TSQ Starts Here)
- Same as standard turtle soup (liquidity purge)
- **TSQ starts with turtle soup and ends with turtle soup**
- Bulls: Purge CRT low → reverse up
- Bears: Purge CRT high → reverse down

#### Phase 2: Model-1
- Confirmation of turtle soup validity
- Wait for close above/below the purge candle
- This candle becomes Model-1

#### Phase 3: Breaker Block
- After Model-1 displacement, market breaks internal structure
- Returns to retest the **last bearish candle** (bullish case) or **last bullish candle** (bearish case)
- That retest candle becomes the **breaker block**
- Entry opportunity at breaker retest

#### Phase 4: OTE (Optimal Trade Entry)
- **Fibonacci 60-75% retracement zone** of the displacement move
- Market pulls back before continuing
- **Requirements for valid OTE trade:**
  1. Clear HTF bias
  2. Liquidity was purged before retracement
  3. Valid Model forming inside OTE zone (CRT, turtle soup, micro Model-1)
- Stop loss: Below protected swing low (buys) / above protected swing high (sells)
- Target: Next liquidity pool or CRT high/low

#### Phase 5: Kiss of Death (KOD)
- **Final turtle soup before market reaches draw on liquidity**
- Signals market is preparing to deliver into target
- The most important phase (according to MadoCRT)
- Also known as "redistribution" in ICT

### Timeframe Alignment for TSQ

| CRT Timeframe | TSQ Observation |
|---------------|-----------------|
| Weekly | 4H |
| Daily | 1H |
| 4H | 15min |
| 1H | 5min |

### Where to Apply TSQ
- Inside CRT range
- From key level to draw on liquidity
- From CRT high to CRT low (and vice versa)
- From OHL(C) structure as reference points

### TSQ Flexibility
- **Strong trending market:** May only show turtle soup + Model-1
- **Complex/slow market:** May show all phases (breaker → OTE → KOD)
- **Goal:** Recognize what's actually there, don't force full sequence

---

## OHLC/OLHC Candle Logic with TSQ

> **Source:** MadoCRT EP 5 - TSQ Phases Using OHLC & OLHC

### Candle Structures
| Structure | Candle Type | TSQ Direction |
|-----------|------------|--------------|
| Open → Low → High → Close | Bullish | Uptrend phases |
| Open → High → Low → Close | Bearish | Downtrend phases |

### OHLC TSQ Sequence (Bullish - OLC)
1. **Open** → Price opens
2. **Liquidity generation** → Turtle soup on short-term low
3. **Expansion** → Aggressive move up (no consolidation = real displacement)
4. **Close above short-term high** → Activates breaker block phase
5. **Return to breaker area** → Breaker block phase
6. **Deep retracement** → OT phase (may act like KOD)
7. **Final turtle soup** → Completes the TSQ cycle

### OLHC TSQ Sequence (Bearish - OHC)
- Same logic, **all phases flipped**
- Bearish turtle soup → expansion down → breaker block below → etc.

### Confirmation Rule
> **"Closes tell the truth. Wicks lie. Closes confirm."**

- Close above = confirm higher prices
- Close below = confirm lower prices
- Wicks can be deceptive — always wait for candle close

### HTF Wick = LTF Expansion
- When HTF hits draw on liquidity and does turtle soup (wick)
- LTF will have at least one short-term expansion move
- One HTF wick can create **multiple LTF CRT opportunities**

### Breaker + OTE Combination
> **When breaker block and OTE combine at the same zone = highest probability**

- Breaker + OTE = strong continuation signal
- Often the strongest phase of TSQ

### Time-Based TSQ on Monthly Candle
| Week | Expected Phase |
|------|----------------|
| Week 1 | Range / Liquidity buildup |
| Week 2 | Manipulation / Turtle soup + Expansion |
| Week 3 | OTE or Kiss of Death |
| Week 4 | Final turtle soup (completes monthly candle) |

### Professional Trading Flow
1. **HTF gives direction** (bias, order flow)
2. **LTF gives execution** (CRT setup, Model-1)
3. Drop to LTF when HTF activates a phase
4. Wait for CRT → Position → Cleaner entry, smaller stop, higher reward

---

## Pattern Rules

### Turtle Soup (Most Important)
1. Range forms (accumulation)
2. Price **falsely breaks** one side (liquidity purge/sweep)
3. Price **reverses** and runs to opposite side (distribution)

### Most Reliable Setups
- CRT forms **near key levels**:
  - Order blocks
  - Fair Value Gaps (FVG)
  - Breaker blocks
  - Rejection blocks
  - Major highs/lows

### Expansion Direction
| After High Purge | After Low Purge |
|-------------------|-----------------|
| Expect downward expansion (SHORT) | Expect upward expansion (LONG) |

---

## Model-1 Entry System

> **Source:** MadoCRT EP 2 - Model-1 Complete Guide

### What is Model-1?
- **Confirmation-based approach** for entering trades
- Low risk, high reward entry technique
- Works perfectly with CRT methodology

### Model-1 Requirements
A valid Model-1 must satisfy **BOTH** conditions:

1. **Purge Liquidity:** Candle(s) dig below lows or above highs (CRT highs/lows OR old highs/lows)
2. **Fill Liquidity:** Candle fills/rebalances an existing order block or FVG (Fair Value Gap)

### Model-1 Types

#### Type A: Purging Liquidity (Order Block Entry)
- Candle purges liquidity by digging below/above a level
- Candle gets **engulfed** (closes opposite direction)
- Price **retests** that specific candle
- At retest → entry is taken

**Sequence:**
1. Liquidity is taken (purge)
2. Close confirms engulf (opposite direction)
3. Retest of purge candle occurs
4. Expansion in our direction

#### Type B: Filling Liquidity (FVG Rebalance Entry)
- Candle fills liquidity by rebalancing an FVG
- That candle gets **engulfed**
- Price retests the engulf candle
- At retest → entry is taken

### When to Use Wick vs Body for Entry

| Scenario | Use |
|----------|-----|
| Price closes just above/below the **open** of purge candle | **Entry at Open (body)** |
| Purge candle is thick/heavy (big body) | **Entry at Open** |
| Price closes above high OR below low of purge candle | **Entry at High/Low (wick)** |
| Purge candle has small body + long wick | **Entry at High/Low (wick)** |

### Model-1 on Higher Timeframes
- Model-1 can be used on HTF for **analysis and context**
- HTF Model-1 shows liquidity draw direction
- Drop to LTF for actual entries aligned with HTF direction

---

## Timeframe Alignment

> **For CRT + Model-1 Entries**

| Higher Timeframe (CRT) | Intermediate (Context) | Lower Timeframe (Entry) |
|------------------------|------------------------|-------------------------|
| Monthly | Weekly | Daily |
| Weekly | Daily | 4H |
| Daily | 4H | 1H |
| 4H | 1H | 15min |
| 1H | 15min | 5min |

**Our Setup:**
- HTF: Weekly (bias, order flow, key levels)
- ITF: Daily (CRT context, refined key levels)
- LTF: 4H (execution with Model-1)

---

## Multi-Timeframe Framework

> **Source:** MadoCRT EP 3 - HTF/ITF/LTF Sync

### Higher Timeframe (HTF) - **Context & Bias**
Focus areas:
1. **Order Flow:** Determine market direction
   - Bullish: Market rejects below low, breaks above high
   - Bearish: Market rejects above high, breaks below low

2. **Bias:** Expectation for next candle
   - Close above previous candle → Expect higher prices
   - Close below previous candle → Expect lower prices
   - Close inside previous candle → Neutral/consolidation

3. **Wick Analysis:**
   - Wick above candle → Expect lower prices
   - Wick below candle → Expect higher prices

4. **Draw on Liquidity:** HTF highs and lows become short-term targets

5. **Key Levels:** FVG, order blocks acting as support/resistance

### Intermediate Timeframe (ITF) - **Narrative & Context**
Focus areas:
1. **Narrative:**
   - **Time-based:** Kill zones, 4H profiles, market profiles
   - **Price-based:** Dealings ranges, turtle soup, PO3, weekly/4H profiles

2. **Context:**
   - Apply CRT for structure understanding
   - Refine key levels from HTF for sharper entries

### Lower Timeframe (LTF) - **Execution**
Focus areas:
1. **Time:** Align with kill zones (no entries outside kill zones)
2. **Entry:** Model-1 confirmation
3. **Stop Loss:** Protected swing high/low (the swing that created Model-1)
4. **Target:** 50% of CRT range OR CRT high/low, minimum 1:2 R:R

---

## Kill Zones

> **Source:** MadoCRT EP 3

### Primary Kill Zones (UTC-5 or UTC-4)
| Kill Zone | Time |
|-----------|------|
| London | 2:00 AM - 5:00 AM |
| New York | 7:00 AM - 10:00 AM |

### Rules
- **Only execute trades within kill zones**
- First check LTF time before taking any trade
- Set chart timezone to UTC-5 or UTC-4
- Ignore setups forming outside kill zones (lower probability)

### Kill Zone Behavior
- Each session has unique market behavior
- London: Often establishes initial direction
- New York: High volatility, strong moves

---

## Entry/Exit Rules

### Complete Trade Pipeline (HTF → ITF → LTF)

#### Step 1: HTF Analysis (Weekly)
1. Identify order flow (bullish/bearish)
2. Determine bias (close comparison)
3. Mark draw on liquidity targets
4. Identify key levels (FVG, order blocks)

#### Step 2: ITF Analysis (Daily)
1. Check kill zone timing
2. Apply CRT framework
3. Refine key levels
4. Look for turtle soup / manipulation setups

#### Step 3: LTF Execution (4H)
1. **Time Check:** Must be within kill zone
2. Wait for CRT high/low purge
3. Identify purge candle
4. Wait for close confirming engulf
5. Entry: Limit order at Model-1 low/high
6. Stop Loss: Below/above protected swing

### Entry Process (Step by Step)
1. Wait for CRT high or low to be **purged**
2. **Identify** the candle that purged the CRT (mark it)
3. Wait for price to **engulf** that candle (close opposite direction)
4. Mark the engulf candle → becomes **Model-1**
5. Place **limit order** at the low of Model-1 candle (for longs) or high (for shorts)
6. Wait for **retest** → trade triggers

### Entry Types
- **Confirmation Entry:** Wait for engulf → place limit order → wait for retest
- **Missed Trades:** Accept that sometimes price won't retest and just takes off (explosive moves)

### Stop Loss Placement
- **Primary:** Below/above the **protected swing** that created Model-1
- Place SL **above Model-1 candle's high** (for longs) or **below Model-1 candle's low** (for shorts)
- Alternative: Place SL above the most recent **swing high** (more conservative)

### Take Profit Targets
- **Primary Target:** 50% of the CRT range
- **Secondary Target:** Opposite end of the CRT range (CRT high/low)
- **Alternative:** Draw on liquidity (HTF targets)
- **Minimum R:R:** 1:2 or 1:3
- **Partial Profits:** Take partials before going for big move

### Trade Reactions After Purge
The market can react in multiple ways after CRT purge:
- **V-shaped reaction:** Quick reversal
- **W-shaped reaction:** Double bottom/top formation
- **Choppy consolidation:** Multiple candles before expansion

---

## Key Level Types (For Setup Confluence)

| Type | Description |
|------|-------------|
| **Order Blocks** | Institutional order zones (previous strong directional candles) |
| **Fair Value Gaps (FVG)** | Imbalances that price fills (three-candle gaps) |
| **Breaker Blocks** | Broken structure that flips role (old support becomes resistance) |
| **Rejection Blocks** | Previous rejection zones |
| **Major Highs/Lows** | Historical significant levels |

### SMT Divergence
- Sometimes price taps key level on one asset while correlated asset has different behavior
- This can cause missed entries - accept it as part of trading

---

## Key Levels (Advanced)

> **Source:** RomeoTPT - CRT Secrets EP 5: Key Levels

### Key Level Definition
> **"A price point at which you expect price to give you a bounce. The bounce can be either counter-trend or the actual low/high of the candle."**

### Three Stages of Key Level Mastery

| Stage | Skill Level | Description |
|-------|-------------|-------------|
| **Stage 1** | Cannot mark correctly | Draw key levels on every point (always wrong) |
| **Stage 2** | Can mark correctly | Identify reversal points accurately, but can't trade them |
| **Stage 3** | Can mark AND trade | Comfortable marking + trading based on price action behavior |

### Key Levels are Higher Time Frame
- Key levels are usually **HTF**
- Need to understand **how LTF price acts at HTF key levels**
- This is how you master entry models

### How Price Acts at Key Levels

#### On the Way to Bullish Key Level
1. **Bearish patterns form all the way down** → CRT pattern traders get wrecked
2. **Convincing bottoming pattern forms** right BEFORE the key level
3. **Fake market structure shift** appears (fake MSS)
4. **KOD turtle soup** at the key level
5. **Then dumps** into the key level
6. **Then flies higher** with true MSS

> **"They create a fake bottom always. Always. There is no exception."**

#### The Trap Before Key Level
```
Bearish patterns down → Fake bottom/MSS → KOD → Dump into key level → True MSS → Higher
```

### Key Level Trade Opportunities

| Trade Type | When |
|------------|------|
| **Journey DOWN to key level** | Sell all the way down to the key level |
| **Journey FROM key level** | Trade after it bounces from the key level |

### The One-Year Rule
> **"Give yourself at least one year from discovering CRT to start making consistent returns."**

- Trading is a career/profession
- Cannot learn in a week
- Either follow by will or by force
- After one year, expect consistent monthly returns

### CRT Pattern Traders Trap
> **"CRT pattern traders will die on the way down to the bullish key level."**

- By the time price reaches key level, pattern traders have no account
- Price then reverses and goes higher

---

## Parameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Trading Timeframe | 4H | User decision |
| HTF Context | Weekly | MadoCRT EP 3 |
| ITF Context | Daily | MadoCRT EP 3 |
| LTF Execution | 4H (Model-1) | MadoCRT EP 2 |
| Risk per trade | 2-3% | User decision |
| Min Risk:Reward | 1:2 or 1:3 | MadoCRT EP 3 |
| Kill Zones | London 2-5 AM, NY 7-10 AM (UTC-5/-4) | MadoCRT EP 3 |

---

## Change Log

| Date | Episode | Changes | Source |
|------|---------|---------|--------|
| 2026-05-10 | EP 1 | Core concepts, CRT types, Turtle Soup pattern, key level importance | MadoCRT EP 1 |
| 2026-05-10 | EP 2 | Model-1 entry system, timeframe alignment, entry/exit rules | MadoCRT EP 2 |
| 2026-05-11 | EP 3 | Multi-timeframe framework, HTF/ITF/LTF sync, kill zones, bias rules | MadoCRT EP 3 |
| 2026-05-11 | EP 4 | TSQ sequence, all phases (turtle soup, model-1, breaker, OTE, KOD) | MadoCRT EP 4 |
| 2026-05-11 | EP 5 | OHLC/OLHC logic, close confirmation rule, breaker+OTE combo, time-based TSQ | MadoCRT EP 5 |
| 2026-05-11 | TS 1 | Turtle soup definition, market maker mechanics, liquidity stops, entry progression | RomeoTPT TS 1 |
| 2026-05-11 | CRT 1 | CRT definition, power of three, 1-2-3 candles, 50% rule, bias rules, entry sequence | RomeoTPT CRT 1 |
| 2026-05-11 | CRT Secrets EP 1 | Model-1 complete rules, thick candle criteria, time theory, weekly timing, FVG enhancement | RomeoTPT CRT Secrets EP 1 |
| 2026-05-11 | CRT Secrets EP 2 | Draw liquidity priority, KOD always present, range consolidation, tape reading tips, SMT warning | RomeoTPT CRT Secrets EP 2 (Live Tape) |
| 2026-05-11 | CRT Secrets EP 2 | KOD detailed rules, KOD mechanics, fuel analogy, KOD location, KOD+FVG combo, bravery rule | RomeoTPT CRT Secrets EP 2 (KOD) |
| 2026-05-11 | CRT Secrets EP 3 | Candle 1-2-3 which to trade, journey inside CRT, LTF anatomy, two dimensions, learning progression | RomeoTPT CRT Secrets EP 3 |
| 2026-05-11 | CRT Secrets EP 4 | Candle anatomy, allowed candles (4H/daily/weekly), fractal nature, trading addiction, core pattern priority | RomeoTPT CRT Secrets EP 4 |
| 2026-05-11 | CRT Secrets EP 5 | Key levels definition, 3 stages mastery, how price acts at key levels, journey trading, one-year rule | RomeoTPT CRT Secrets EP 5 |
| 2026-05-11 | CRT Secrets EP 6 | SMT definition, SMT pairs, 4 uses, confirmation process, SMT trap avoidance, candle polarity | RomeoTPT CRT Secrets EP 6 |

---

## Tape Reading & Live Application

> **Source:** RomeoTPT - CRT Live Tape-Reading Session

### Draw Liquidity Priority Rule
> **"The draw liquidity is paramount. It comes first."**

- **Never ignore the target** for pattern trades
- Ignore all bullish patterns on the way down to a **bearish target**
- Ignore all bearish patterns on the way up to a **bullish target**
- **Only look for patterns aligned with the target direction**

### Pattern vs System Trading
| Pattern Trader | System Trader (CRT) |
|----------------|---------------------|
| Trades every pattern | Trades only aligned with target |
| Gets stopped out repeatedly | Waits for target-aligned setup |
| Blames the system | Accepts accountability |

### Order Flow Analysis
In bearish market:
- **Highs are being used** to stop out sellers, sucker in new buyers, then dump
- Old highs become traps: "pop above, dump"

### Kiss of Death (KOD) Always Exists
> **"There's always always always a kiss of death turtle soup before dumping into the target. It's never not there."**

- KOD appears just before reaching draw liquidity
- **KOD = final trap before target delivery**

### KOD Warning Sign
> **"You don't want them to go above a kiss of death turtle soup."**

- If price **closes above KOD wick** = warning sign (possible SMT)
- May indicate target won't be reached

### Range Consolidation Behavior
> **"They like to wiggle around, create hope, then dump straight into it."**

- Price never goes straight to target
- Creates **mid-move consolidation** and hope
- Grind up/down = designed to trap more traders
- **Patience is critical** — wait for target delivery

### SMT (Symbolic Market Theory)
> **"One asset class taking a high/low while the other asset class does NOT take the high/low."**

- **Origin:** First introduced by Charles Dao in the 1800s (not ICT origin)
- SMT = **Secret signal** from smart money to smart money
- If one asset takes the high and the other doesn't → **weakness**
- **Focus on one asset = miss the signal**

### SMT Pairs (Main Ones)
| Asset | SMT Pair |
|-------|----------|
| Euro | Dollar (inverse) |
| ES (S&P) | NQ |
| Dow Jones | - |
| Bitcoin | Ethereum |
| Gold | Silver |

### SMT Uses (4 Main)
| # | Use | Description |
|---|-----|-------------|
| 1 | **Fill FVGs** | One fills FVG, other doesn't = SMT fill |
| 2 | **Confirmation** | Confirm trade direction using correlated pair |
| 3 | **Leave Equal Highs/Lows** | Creates equal highs/lows pattern |
| 4 | **CRT Signal** | Different CRT behavior between pairs |

### SMT Confirmation (Critical)
> **"If you see SMT, ALWAYS wait for both confirmations."**

| Confirmation | What It Is |
|--------------|------------|
| **1st Confirmation** | Model-1 (close opposite the thick candle that pushed into low/high) |
| **2nd Confirmation** | True Market Structure Shift (MSS) on LTF |

### SMT Confirmation Process
```
SMT Signal Detected
    ↓
Wait for Model-1 (first confirmation)
    ↓
Wait for True MSS (second confirmation) for further expansion
```

### SMT Trap Avoidance
> **"If you see SMT and blindly buy, you get wrecked. Always wait for confirmation."**

- See asset class A take the low, B NOT take the low
- If you blindly buy A → get wrecked
- **Solution:** Wait for confirmation (Model-1 + MSS)

### Candle Polarity
- **Down-Close candles** = True support
- **Up-Close candles** = True resistance
- If one works, the other won't

### Manipulation at End of Candle
> **"If manipulation happened at the end of a previous candle, expect distribution to happen in the next candle with minimal manipulation."**

### Model-1 Counter-Trend Behavior
> **"Even if your bias is wrong, Model-1 usually gives you a counter-trend move."**

- Model-1 can work against bias (gives reaction)
- But we are **not counter-trend traders** — we trade with the trend
- We wait for the right trend start, not chase counter-moves

### Tape Reading Tips
1. **Larger screen = better** — see more context
2. **Zoom out when LTF is noisy** — look at 4H for clarity
3. **Watch every candle** — observe market maker manipulation
4. **Mark rejection zones** — see where dumb money gets trapped

### Initial Target Strategy
| Step | Action |
|------|--------|
| 1 | Take **partial profit** at initial target (50% or FVG) |
| 2 | Let remainder run to main target |
| 3 | Be content with the move — close charts, come back later |

### Range vs Trend Rule
| Market State | What to Do |
|--------------|------------|
| **Ranging** | Don't look for trending moves — you'll go insane |
| **Trending** | Don't force range behavior |

> **"Never anticipate a trending move in a ranging market, and vice versa."**

### Target Zones (What Retail Targets)
- Retail traders place buys at old support levels
- We **target the levels they're trying to enter at**
- Classic support/resistance is a trap

### Patience Requirement
- **Planning a trade**: 1 minute max
- **Executing**: 2 seconds
- **Waiting**: Hours/days

> **"Patience is paramount to a long-lasting lucrative trading career."**

### Accountability Rule
> **"When you fail, it's always your fault, never the system's. Blame yourself, take accountability, and you're more likely to improve."**

---

## Kiss of Death (KOD) Turtle Soup

> **Source:** RomeoTPT - CRT Secrets EP 2: The Kiss of Death

### What is KOD?
> **"The final turtle soup before the target is hit."**

- **Last turtle soup** before price delivers into draw liquidity
- Usually a **very fast, vicious move** into target
- **KOD always exists** before any target delivery

### KOD Sequence
```
CRT High → Turtle Soup → 50% Bounce → KOD Turtle Soup → DUMP to CRT Low
```

### KOD Mechanics (Why It Works)
1. Market makers **push price above** engineered liquidity pool
2. This **stops out previous shorts**
3. This **entices new longs** (breakout traders, ICT buyers)
4. Uninformed/retail money piles in
5. Market makers **dump** into target

### KOD = The Fuel
> **"Before any large price move, there is a turtle soup. Turtle soup is the gas, the fuel that allows price to move."**

- No turtle soup = lots of chopping (no fuel)
- Turtle soup = price ready to move
- KOD specifically fuels the final move to target

### Where KOD Occurs
| Location | Description |
|----------|-------------|
| **Lower 25% of range** | Common KOD zone before target |
| **OTE Zone** | KOD can appear as optimal trade entry |

### KOD + FVG Confluence (Highest Probability)
| Combination | Signal |
|-------------|--------|
| Bearish FVG + KOD above old high | High probability SELL |
| Bullish FVG + KOD below old low | High probability BUY |

### How to Trade KOD
| Step | Action |
|------|--------|
| 1 | Identify CRT high/low |
| 2 | Wait for initial turtle soup |
| 3 | Wait for 50% bounce |
| 4 | Watch for KOD turtle soup |
| 5 | Find Model-1 on LTF for entry |
| 6 | Risk above KOD, reward at target |

### The Bravery Rule
> **"Selling the big bullish candles is something only experience can teach you."**

- Train yourself to **sell big up-close candles**
- Train yourself to **buy big down-close candles**
- Within rules, of course

### Why People Fail at KOD
| Mistake | Why It's Wrong |
|---------|----------------|
| Buying at big bullish candle | Market makers using that liquidity |
| Not recognizing KOD | Mistake KOD for regular turtle soup |
| Not following CRT rules | System is perfect, user error |

### CRT Priority Awareness
> **"Knowing CRT exists is an advantage. Having a pending CRT down there might save you money or make you money."**

### Two Dimensions of Analysis
| Dimension | Description |
|-----------|-------------|
| **HTF** | Candle shape (what's forming) |
| **LTF** | Candle slope (how it's moving) |

### Homework (For Practice)
- **Reverse engineer** a bullish KOD turtle soup
- **Forecast live** a bullish KOD turtle soup
- **History is a goldmine** — it repeats itself

### Quick Recap
```
CRT High → Turtle Soup → 50% → KOD Turtle Soup → Target
```

---

## CRT Journey (Candle 2-3 Anatomy)

> **Source:** RomeoTPT - CRT Secrets EP 3: The Journey

### Which Candle to Trade?

| Candle | For Beginners | For Advanced |
|--------|---------------|--------------|
| **Candle 1** | Avoid | With extreme caution |
| **Candle 2** | **AVOID** - Very difficult | Only extremely advanced students |
| **Candle 3** | **100% FOCUS** - Practice this first | Primary trade |

> **"Trade candle number 3. Only extremely advanced students can trade candle number 2."**

### The Journey Inside a CRT
> **"From turtle soup to target, the journey inside a CRT includes: Turtle Soup → Model Number One → Breaker → OTE → Kiss of Death Turtle Soup."**

### Fixed Price Moves in Every CRT (Always Present)
| Phase | Description | Priority |
|-------|-------------|----------|
| **Turtle Soup** | Almost always there, always present | Fixed |
| **Model-1** | Favorite entry | Fixed |
| **Breaker** | True market structure shift | Fixed |
| **OTE** | Optimal trade entry | Fixed |
| **KOD** | Last turtle soup before target | Fixed |

### The Journey Sequence (Bullish CRT)
```
CRT Low (Accumulation)
    ↓
Turtle Soup at the low (accumulation phase)
    ↓
Model-1 (confirmation)
    ↓
Breaker (true MSS)
    ↓
OTE (pullback entry)
    ↓
KOD Turtle Soup (final trap)
    ↓
Target (CRT High)
```

### Two Dimensions of CRT
| Dimension | What It Shows |
|-----------|--------------|
| **Outside (HTF)** | Candle shape - accumulation, manipulation, distribution |
| **Inside (LTF)** | Anatomy - turtle soup, model-1, breaker, OTE, KOD |

### Two Targets in Price
| Target Type | Description |
|-------------|-------------|
| **Liquidity Pool** | Attack a high or low |
| **Imbalance** | Rebalance / fill gap (which is also a LTF high/low) |

> **"Price moves for two reasons only: to attack a liquidity pool (high/low) or to rebalance an imbalance."**

### True Market Structure Shift (MSS)
- Every CRT has a **true MSS by nature**
- Marked by: Turtle soup on candle 1 + Breaker
- This confirms the trend shift

### Smart Money Accumulation Behavior
> **"When you're trying to catch the exact high or low, price becomes slow and lethargic. Why? Because smart money is accumulating."**

- Slow price = accumulation phase
- Sudden massive move = distribution complete

### Risk Management Reminder
> **"If you blow your account on one bad setup, you have bad risk management."**

### Learning Progression
1. **Start:** Trade candle 3, tape read candle 2
2. **Master:** When you master candle 3, then proceed to candle 2
3. **Advanced:** Only for extremely advanced students (1%)

### What You Will Always See on LTF (Inside CRT)
```
✓ Turtle Soup (given, always)
✓ True MSS (breaker)
✓ Model-1
✓ KOD before CRT high/low is reached
```

### Key Insight
> **"A higher time frame gap = a lower time frame high or low."**

- All gaps are just highs/lows on different timeframes

---

## Candle Anatomy

> **Source:** RomeoTPT - CRT Secrets EP 4: Candle Anatomy

### First Question Before Trading
> **"Before thinking about CRT pattern, turtle soup, Model-1, breaker, KOD — the first question is: What candle am I trading?"**

### Allowed Candles to Trade (Beginners to Advanced)

| Level | Candles Allowed |
|-------|-----------------|
| **Beginner** | 4H candle |
| **Intermediate** | 4H + Daily |
| **Advanced** | 4H + Daily + Weekly |

> **"Stop at 4H, Daily, Weekly. Only after advancing, ascend to monthly."**

### All Candles Are Identical
| Property | Same |
|----------|------|
| Structure | Open, High, Low, Close |
| Mechanisms | Same |
| Timing patterns | Same |

> **"All candles look and print the exact same way. The only difference: some print faster than others."**

### Fractal Nature of Candles
- Monthly = slower 4H
- 4H = slower 1H
- All have same anatomy
- 100 hourly candles = ~100 weeks of data
- **Use LTF for analysis (not trading)** to gain experience faster

### Decision Hierarchy
```
1. Which candle am I trading? (4H, Daily, Weekly)
2. Then look for CRT/Turtle Soup pattern
3. Then look for entry models (Model-1, breaker, KOD)
4. Entry is LAST
```

### Trading Addiction Warning
> **"The best way to make money long-term is through less trades."**

| Type | Trades | Result |
|------|--------|--------|
| Gamblers | 100-200/day | Losses |
| Wealthy traders | 1-2/week | Profits |

### Lower Time Frame Rule
| Purpose | Use |
|---------|-----|
| **Analysis** | Yes - gain experience faster (100 hourly = 100 weeks) |
| **Trading** | No - only for extremely advanced |

### Core Pattern (First Priority)
| Direction | Pattern |
|-----------|---------|
| **Bearish** | Open → Turtle Soup → Dump |
| **Bullish** | Open → Dump → Turtle Soup → Pump |

### Homework
- Conceptualize and visualize candles from opening to closing
- See how all candles look the same (fractal)
- Practice identifying which candle you're trading first

---

## Candle 3 Trading (EP 7)

> **Source:** RomeoTPT - CRT Secrets EP 7: Candle 3

### Candle 1 vs Candle 3 - Critical Difference

| Candle | Contains | When to Trade |
|--------|----------|---------------|
| **Candle 1** | Model-1 (confirmation) | Advanced only |
| **Candle 3** | OTE (Optimal Trade Entry) | Primary trade for all levels |

> **"Candle number 3 will have the OTE. Model number one is in candle number one."**

### Wait for Candle 2 to Close

- **Never trade during Candle 2** - it's still forming
- Wait for Candle 2 to **close completely**
- Only then enter trades on **Candle 3's open**
- Candle 3 is the **trading zone**

> **"You wait for candle number two to close, then you trade candle number three's open."**

### OTE Behavior When Trend is Strong

| Scenario | Price Behavior |
|----------|----------------|
| **Normal** | Price reaches 50% retracement in OTE zone |
| **Strong Trend** | Price **won't reach 50%** - goes to lower fib levels (e.g., 25%, 38%) |

> **"If the trend is really strong, it won't go all the way to 50%. It will go to lower fib levels."**

### Why OTE is About Luring Liquidity

> **"OTE is about luring liquidity... the OTE is about luring not reaching the zone itself."**

- OTE zone acts as **bait for liquidity** (stop orders)
- Price doesn't need to reach exact 50% to succeed
- It's a **range-based approach**, not exact level

### Candle 2 Characteristics - Avoid Trading

| Property | Description |
|----------|-------------|
| **Speed** | Slow, choppy, lethargic |
| **Difficulty** | Even advanced traders prefer Candle 3 |
| **Trading** | Not recommended for beginners |

> **"Even some advanced traders like myself, we don't like trading candle number two because it's slow and choppy and lethargic."**

### SMT Confirmation Before Trading

- Always confirm with **SMT (Symbolic Market Theory)** before entry
- Prevents trading in **wrong direction**
- Confirms weakness/strength of correlated asset

> **"SMT confirmation prevents you from trading the wrong direction."**

### Universal Journaling Law

| Result | Action |
|--------|--------|
| **Win** | Journal → Repeat |
| **Lose** | Journal → Avoid that setup |
| **Miss** | Journal → Catch next time |

> **"The universal journaling law: you win, you journal, you repeat. You lose, you journal, you avoid. You miss, you journal, you catch it next time."**

### Candle 3 Summary for Beginners

1. Wait for Candle 2 to close
2. Trade the open of Candle 3
3. Look for OTE (50-75% retracement zone)
4. If strong trend, accept lower fib entries
5. Use SMT confirmation
6. Journal every trade

---

## When Does CRT Fail? (EP 8)

> **Source:** RomeoTPT - CRT Secrets EP 8: When does CRT fail?

### Three Main Reasons CRT Fails

| # | Reason | Description |
|---|--------|-------------|
| 1 | **SMT** | SMT can stop targets from being hit |
| 2 | **Already hit 50%** | Target #1 is 50%, after that it's valid either way |
| 3 | **Wrong CRT Selection** | Picking bearish CRTs in bullish trend or vice versa |

### Reason #1: SMT Stops Target

> **"SMT can be used to stop targets from being hit."**

#### How SMT Stops CRT:
- CRT is setting up to hit target
- But SMT forms **before** target is reached
- This **stops price** from completing the original CRT
- Creates **new CRT** in opposite direction

#### How to Identify SMT (Candle SMT):
1. Look at two consecutive candles
2. One candle **turtle soups**, one **does not**
3. That's the SMT divergence
4. **Confirm with Model-1** or **true MSS targeting new highs**

> **"You go and you look at the candle SMT between this candle and this candle. That's an SMT. One candle turtle souped and this candle did not turtle soup."**

#### Key Confirmation Candle:
- The **down close candle** that liquidated the old low
- Usually the most consistent catalyst of large price moves
- This specific candle caused the rally instead of CRT completion

#### Bitcoin Example:
- Bitcoin had valid CRT with turtle soup
- Expected to attack CRT low
- Instead: came close, then rallied to new all-time highs
- **Why?** SMT between this CRT low
- On the way down, they created another CRT with SMT
- SMT confirmation (Model-1) made it bullish - no reason to be bearish after that

> **"They're about to go down into this CRT low, but because of the SMT, they were stopped... Instead, there was another CRT which worked right there."**

#### Trading Rule:
- If CRT has SMT confirmation **before** hitting target
- Don't force your bias - follow the market
- Go with the SMT direction (higher/lower)

### Reason #2: Already Hit 50%

> **"In CRT, target number one is always 50% of the candle."**

#### The 50% Rule:
| Scenario | Outcome |
|----------|---------|
| Price reaches 50%, then reverses | **Valid CRT** - Target #1 achieved |
| Price reaches 50%, continues to low | **Valid CRT** - Full CRT completed |

#### Both Are Correct:
- **Either outcome is valid**
- **Both are within the rules**
- After reaching 50%, monitor price action:
  - Ready for continuation? → Go to low
  - Reversing? → Take profit at 50%

> **"It either goes down to the 50% and then reverses higher, which is a valid CRT. It didn't fail because it fulfilled the rule, which is 50%. Or it can go down and continue and complete the CRT."**

#### Lifetime Trading Strategy:
> **"Those who focus on taking the CRT from the high or the low to the 50% and that's all they trade for the rest of their lives, then they can build a fantastic trading career just on that."**

- Trade: high/low → 50% only
- Simpler, more consistent
- Works for life

### Reason #3: Wrong CRT Selection

> **"You pick bearish CRTs on the way up to a bullish target or you try and force bullish CRTs on the way down to a bearish target."**

#### The Rule:
| Direction | What to Avoid |
|-----------|---------------|
| **Bullish Trend** | Don't pick bearish CRTs |
| **Bearish Trend** | Don't pick bullish CRTs |

#### Why It Fails:
- Counter-trend trading works **sometimes**
- But it's less accurate and consistent
- Better results: **stick to CRTs with the trend**

> **"Avoid picking bullish CRTs and pick bearish CRTs... Stick to the CRTs with the trend and vice versa."**

#### HTF vs LTF Alignment:
- Don't buy bullish CRTs on LTF within HTF bearish CRT
- Don't sell bearish CRTs on LTF within HTF bullish CRT
- Always align with higher timeframe direction

### Mindset Shift (Important)

> **"The strategy works fine. It's simply you being unable to identify the strategy working because you lack the knowledge."**

| Mindset | Reality |
|---------|---------|
| "Strategy failed" | You failed to identify it working |
| "Strategy is wrong" | **You** are wrong, go fix yourself |
| System is perfect | Errors are always user fault |

#### Key Principles:
- **The system is perfect** - comes from market makers themselves
- **Expect to lose** - expect strategy to not work sometimes
- **More you learn, more you earn**
- **Journal everything** - wins, losses, misses

> **"The more you learn, the more you earn... The system is perfect. The system comes straight from the market makers themselves. It is perfect."**

---

## Connecting the Dots (EP 9)

> **Source:** RomeoTPT - CRT Secrets EP 9: Connecting the dots

### Trade Framework (Process Before Any Trade)

| Step | What to Do |
|------|-------------|
| **1. Higher Time Frame** | Analyze candle shape and narrative |
| **2. Market Profile** | Analyze highs and lows |
| **3. Entry Model** | Look for entry LAST (after confluences) |

> **"First the higher time frame candle shape and narrative and then market profile which is the highs and lows."**

### HTF Candle Shape Analysis

1. **Higher time frame candle** - Expecting some sort of retracement?
2. **Daily heading into old liquidity pool** - Some reaction expected
3. **Price stabbing into old low** - Closing above high that broke low = true MSS
4. **After true MSS** - Look for retrace into area between high and low, then pump higher

> **"After this close above, look for them to retrace into this area between the high and the low and then pump higher."**

### SMT Application

| Situation | Action |
|-----------|--------|
| ETH attacks low, BTC does not attack and rallies | **SMT** - expect BTC not to go back into low |
| Higher time frame bullish | Only look for **bullish SMTs** |
| Higher time frame bearish | Only look for **bearish SMTs** |

> **"SMT equals expansion... Only look for bullish SMTs in a higher time frame bullish market. Only look for bearish SMTs in a higher time frame bearish market."**

### Every Entry is Model-1 or True MSS

> **"Every single entry you will ever take is either going to be a model number one or it's going to be a true market structure shift."**

| Entry Type | Description |
|------------|-------------|
| **Model-1** | Confirmation candle (thick candle stabbing into old high/low, close opposite direction) |
| **True MSS** | Break above high that broke low, or break below low that broke high |

### Entry Area (Optimal Zone)

| Area | Description |
|------|-------------|
| **Good Buy Area** | Between the high and low of the true market structure shift |
| **Stop Loss** | Low of the turtle soup (unlikely to get turtle souped) |

> **"The area between the high and the low of the true market structure shift is a good area to buy with the stop loss being the low of the turtle soup."**

### Exit Strategies

| Method | Description |
|--------|-------------|
| **Time-based** | Exit at a certain time |
| **Price-based** | Exit at a certain price level |

> **"You exit either based on time or you exit based on price level. Both are valid."**

> **"Every exit is an entry."**

### Trade Example: Bitcoin Flash Crash

1. **Flash crash** = Monthly CRT playing out
2. **Three drives** → Turtle Soup → Turtle Soup of Turtle Soup → Crash to CRT low
3. **Old low with FVG under it** = expect bullish reaction
4. **Model-1**: One specific candle that liquidated the old high (not a zone, one candle)
5. **Weekly candle** closed below up-close candle that liquidated old high
6. **Even if bearish**: Expect dump into pump into at least this candle

> **"It's this one specific candle right over there... That's the one when they close below it, then it dumps soon after."**

### Key Insights

- **Price moves in patterns**: Range → Trend → Range → Trend → Range
- **When hitting major target**: Especially around all-time highs with FVG under → expect reaction
- **One specific candle**: Not zones or bunches of candles - single candle model-1
- **Trade timeframe**: Catch a portion of one daily candle (e.g., Tuesday London session)
- **Trade from point A to B**: Based on HTF candle shape and market profile

### Market Profile Process

1. HTF candle shape and narrative
2. Identify old liquidity pools
3. Find where price stabbed into old low
4. Look for close above the high that broke the low (true MSS)
5. Enter in area between that high and low

---

## A Clean Close (EP 10) - Final Episode

> **Source:** RomeoTPT - CRT Secrets EP 10: A clean close

### This is the Official Public CRT Mentorship
- This series is the official free CRT mentorship on YouTube
- Points to this as the source for anyone asking where to learn CRT
- Better than every paid course out there

### Key Teaching Instructions

| Principle | Description |
|-----------|-------------|
| **Watch multiple times** | With each watch, you'll catch things missed before |
| **Pen and pad in hand** | Always take notes while watching |
| **Stay hungry for more** | Never be content with watching once |
| **Discipline > Motivation** | Motivation is temporary, discipline is forever |

> **"Watch each episode multiple times with a pen and pad in hand."**

> **"Motivation is temporary and discipline is forever."**

### Common Mistakes to Avoid

| Mistake | Why It's Wrong |
|---------|-----------------|
| **Strategy hopping** | Leads to never mastering anything |
| **Mentor hopping** | Don't stray from the source |
| **Arrogance** | "Above every knowledgeable one there is one more knowledgeable" |

> **"There are some advanced topics I touched on but didn't go too deep. For example, the drawn liquidity and a very common one is how to pick the correct key level."**

### Advanced Topics (In Book)

These will be covered in depth in the book (Feb 1, 2026):
- **Drawn liquidity** - How to identify and trade around it
- **Key level selection** - How to pick the correct key level (most important)
- **Journaling** - Mistake correcting
- **And more**

> **"One of the most important things in my book is how to choose the correct key level."**

### Final Message

> **"Don't be fooled by scammers claiming to shorten the CRT learning curve."**

- Stick to the source (RomeoTPT)
- Follow the content on social media (Twitter, Telegram, YouTube, Instagram)
- Content is summarized in CRT University and the book

### What's Coming in 2026

- **Book release**: February 1, 2026 (limited quantity)
- **2026 mentorship**: Potentially starting Q2 (comment to request)
- This will be the most complete system shared to date
- New students will be fast-tracked to success
- Existing successful students will gain even more

---

## Tape Reading Session (Video 14)

> **Source:** RomeoTPT - CRT Live Tape-Reading Session (2)

### Target Trap Behavior

> **"It's really cute when they go near the target itself... they come really close to the target, and then they go and they wiggle around and try and pretend like they're not going to hit it."**

| Phase | Behavior |
|-------|----------|
| **Approach** | Price comes close to target (major liquidity pool) |
| **Pretend** | Bounces around, creates fake MSS, gives false hope |
| **Trap** | Many novice traders fall into this trap |
| **Execution** | Then viciously dump/straight down to target |

> **"Every single time before they hit a target... they're going to pretend like they're not going to hit it. That's part of the game."**

### Fake Market Structure Shift

> **"You see a market structure shift and this is a fake market structure shift right here... it is going to be completely ignored and they're going to go straight down to the target."**

| Indicator | What It Means |
|-----------|---------------|
| **Fake MSS** | Any bounce/rally that happens before target |
| **Why fake** | Interest is at the target, not the bounce |
| **Time** | May take 10-15 min or half an hour |
| **Result** | All fake → straight down to target |

### Tape Reading Skill

> **"The skill of being able to anticipate how price will play out is something you can't put a price tag on... you have to learn by going into the charts and sitting down and getting used to the charts."**

| Tape Reading Steps |
|-------------------|
| 1. Become friend of the charts |
| 2. Know charts like back of your hand |
| 3. Sit down and familiarize yourself |
| 4. Practice anticipating price moves |

### Post-Entry Behavior (Critical)

> **"One thing is knowing how to plan a trade. One thing is knowing how to press the button which is the easiest thing. But another thing is after entering the trade, how do you react to each price movement?"**

Trading breakdown:
- **Planning**: ~1 minute
- **Pressing button**: 1 second
- **Waiting for trade**: From entry to exit (the real trading)
- **Emotional regulation**: During the wait

> **"Waiting for the trade to play out from A to Zed... and controlling and regulating your emotions throughout the process... That is trading."**

### Journaling Levels (Most Complete Form)

| Level | Description |
|-------|-------------|
| **1. Basic** | Before, during, after (most don't even do this) |
| **2. Pictures** | Add screenshots to notes |
| **3. Blend** | Pictures + notes combined |
| **4. Emotions** | Factor in your emotional state |
| **5. Recording** | Record trades (especially scalps) - highest level |

> **"The most basic level is you know before during after and even that even the most basic level of journaling no one does it."**

> **"The highest level of journaling is recording your trades... watching the candles minute by minute."**

### Market Profile Tape Reading

> **"On the way down... all the way down, you should notice is highs and lows. Look at the highs and look at the lows."**

| Indicator | Meaning |
|-----------|---------|
| **Highs being turtle souped** | More downside coming |
| **Lows being broken** | More downside coming |
| **Continue until** | They no longer want to go that direction |

> **"As long as the target is down here, they're going to keep turtles souping highs and breaking below the lows until they no longer want to go down."**

### Trading is 80% Behavior

> **"Trading is 80% behavior and 20% technicals... regulating your behavior is one of the most valuable skills you learn on your way to becoming a profitable trader."**

### Natural Human Reaction (Trap)

| Reaction | What Happens |
|----------|--------------|
| **On bounce** | "Is this the bottom? Is it over?" |
| **On dump** | "Will they hit the target?" |
| **This is** | Human nature, not psychopath |
| **Result** | Neophyte traders get trapped |

> **"It's cute when they go near the target... they wiggle around and try and pretend like they're not going to hit it... this is a trap in which many neophy traders fall into."**

---

## SpeculatorFL - Axis Framework

> **Source:** SpeculatorFL - Chapter 01: Introduction to Core Concepts - ICT and CRT

### Four Foundational Pillars

| Pillar | Purpose |
|--------|---------|
| **Time Frame Alignment** | Structure time frames |
| **Market Structure** | Define direction + detect shifts |
| **Market Profiles** | Understand market phase |
| **SMT** | Confirm with correlated asset |

> **"Each one of these concepts supports the next one like bricks on a wall. If you remove just a single brick, the whole system starts to fall."**

---

### Time Frame Alignment

#### The Model's Purpose
> **"My model is built in a way that its main purpose is to exploit the range expansion that occurs within a day or within the daily candle."**

#### Three Time Frame Structure

| Time Frame Level | Time Frames Used | Purpose |
|------------------|-----------------|---------|
| **Higher Time Frame** | Monthly, Weekly, Daily | Establish directional bias + identify draw liquidity |
| **Contextual Time Frame** | 4H only | Define market context + dealing range |
| **Lower Time Frame** | 15min only | Execution (entries) |

> **"The higher time frame is the only part where you can use multiple time frames to achieve a single objective. Using multiple time frames for contextual or lower time frame adds complexity and reduces mechanicality."**

#### Why This Structure Works
- Works for consistently profitable traders (ICT, Romeo, SpeculatorFL)
- Mechanical and repeatable
- Optimal for exploiting daily candle range expansion

---

### Market Structure

#### Definition
> **"Market structure is the basic framework or the fundamental framework that price moves within. This is where you start to begin to make sense of the direction of price."**

#### Two Core Components

| Component | Description |
|-----------|-------------|
| **1. Define Structure** | Identify current trend (higher highs/higher lows OR lower highs/lower lows) |
| **2. Confirm Structural Shifts** | Detect breaks in trend - when underlying trend changes |

> **"Both components are based on tracking key highs and key lows. Not every candle, not every swing, but just key highs and key lows."**

#### Key Highs and Lows (Objective Definition)

| Term | Definition |
|------|------------|
| **Key High** | A high that broke above a previous high (which became a key low) |
| **Key Low** | A low that broke below a previous low (which became a key high) |
| **Normal High/Low** | Has NOT broken any structure yet |

> **"A high or a low becomes key when it's the one that most recently broke structure."**

#### How to Define Structure Objectively

| Trend | Behavior |
|-------|----------|
| **Uptrend** | Price consistently breaking above highs AND rejecting below lows |
| **Downtrend** | Price consistently breaking below lows AND rejecting above highs |

> **"Most people eyeball it and say 'it's going up'. That's not objective. That doesn't work in real market conditions."**

#### Valid Structural Shift

| Requirement | Description |
|-------------|-------------|
| **Must be key level** | Occurs at a premium key level |
| **Must be key high/low** | Not just any high/low - must be a key high or key low |
| **Must close** | Price must close below key low or above key high |
| **Optional** | SMT confirmation with correlated asset |

> **"A structural shift is only valid when it happens in the right context, at a key level. Otherwise it's just a simple liquidity purge below a low."**

#### Live Example: Bullish Structure
- Price breaks above a high → that low becomes key
- Price rejects below lows → still bullish
- Price breaks above highs consistently → bullish structure continues
- Until price closes below a key low → structural shift (bearish)

#### Live Example: Invalid vs Valid Shift
- Price closes below a **normal low** → NOT valid (just liquidity purge)
- Price closes below a **key low** (that broke above a high) → VALID structural shift

> **"Unless a structural shift happens, your expectation from price would be to continue the structure. You can't just force price to break structure because you want it to."**

---

### Market Profiles

#### Why Market Profiles?
> **"Market structure tells you the basic trend framework but it doesn't tell you what the market is actually trying to do on a daily basis. Price doesn't move in a straight line - it moves in phases."**

| Market Structure | Market Profiles |
|------------------|-----------------|
| Tells you the **direction** | Tells you the **phase** |
| Directional idea | Refines + confirms/invalidates direction |
| Incomplete alone | Complements structure |

#### Basic Profiles Framework

| Profile | Description | Potential Outcomes |
|---------|-------------|-------------------|
| **Ranging Profile** | Consolidation/sideways | Expansion only |
| **Expansion Profile** | Breakout in direction | Retracement, Consolidation, or Reversal |
| **Retracement Profile** | Pullback into range/level | Expansion only |
| **Reversal Profile** | Trend change | Starts new structure |

#### Power of Three Framework (Advanced)

| Profile | Description |
|---------|-------------|
| **Ranging** | Consolidation |
| **Manipulation** | Takes out liquidity (above range high or below range low) |
| **Expansion** | The real move |

> **"Power of Three narrows down the four profiles into just three and gives a much more refined view."**

#### Profile Sequence Example
```
Ranging → Manipulation → Expansion → Minor Retracements → Expansion
```

> **"Each profile has its own sequence logic, pattern of behavior, and likely outcomes. Profiles are what add depth to your structure reading."**

#### Profile as Filter
- Even in bullish structure, not all profiles are tradable
- Some profiles/phases are lower probability
- Market profiles help filter which conditions to trade

> **"If you're not aware of market profiles, you would incorrectly try to trade every sort of price action and you'd end up losing."**

---

### Liquidity Metrics

> **"Liquidity metrics helps us identify where major pools of liquidity exist and how price is interacting with them."**

#### How Concepts Integrate

| Step | Concept | What It Gives You |
|------|---------|-------------------|
| 1 | **Market Structure** | Directional idea |
| 2 | **Market Profiles** | Phase/cycle understanding |
| 3 | **Liquidity Metrics** | Refine directional idea → directional **bias** |

> **"These concepts do not work in isolation. When they are used alone, they bring meaninglessness. When built on top of each other, that's when it brings clarity."**

---

## SpeculatorFL - Chapter 02: The Axis Framework

> **Source:** SpeculatorFL - Chapter 02: The Axis Framework - ICT and CRT Integration

### The X System is a Web (Not a Linear Checklist)

> **"Don't think of the X system as some sort of a linear checklist of concepts that you apply one after the other. That's the wrong approach. The X model is a web. It's a complete network."**

| Property | Description |
|----------|-------------|
| **Integration** | Each concept feeds into another, relies on, and confirms each other |
| **Systematic** | Frameworks have step-by-step procedures using multiple concepts together |
| **Confirmation** | Concepts confirm each other to establish objectives (like directional bias) |
| **Rejection** | Concepts systematically reject each other through proper logic → invalidation |

> **"Trading isn't just about when to trade but also when not to trade."**

---

### Three Layers of the X Framework

| Layer | Purpose | Where It Happens |
|-------|---------|------------------|
| **1. Directional Bias Layer** | Establish initial direction for the day | Higher time frames (Monthly/Weekly/Daily) |
| **2. Context Layer** | Confirm or reject bias, identify market context | Intermediate time frame (4H) |
| **3. Execution Layer** | Entry trigger and entry model | Lower time frame (15min) |

> **"The real edge comes from proper alignment and proper integration."**

---

### Layer 1: Directional Bias Layer

This is where your trade idea begins. The objective: determine directional bias for the day OR identify draw liquidity on the higher time frame.

#### Three Components

| Component | Description |
|-----------|-------------|
| **1. Time Frame** | Define which time frames matter |
| **2. Structure** | Determine market direction using concepts |
| **3. Narrative** | Build a cohesive story (origin + destination) |

#### Time Frames for This Layer
- **Monthly** → **Weekly** → **Daily** (refine down each level)
- Start with monthly at start of week, build directional idea
- Refine to weekly, then to daily
- By end: clear directional bias for the day

#### Structure Component (Secondary + Primary Concepts)

| Concept Type | Concepts | Used On |
|--------------|----------|---------|
| **Secondary** | Quarterly Framework, Seasonal Tendencies | Monthly only |
| **Primary** | Liquidity Metrics, Market Structure, Market Profiles | Monthly, Weekly, Daily |

> **"Secondary concepts have very little to do with charts or candles. Their idea is derived from past historical behavior."**

##### Quarterly Framework
- Look at price action in past 3-4 months
- Determine predominant direction
- Underlying premise: every 3-4 months price shifts into a new trend

##### Seasonal Tendencies
- Look at seasonal tendency chart for an asset
- Shows how asset behaved in past 20-30 years throughout the year
- Combine with quarterly framework for macro directional context

#### Narrative Component

> **"Structure gave you the direction, but narrative gives you the story line. It helps you answer: where is that bullish move going to originate from?"**

| Question | Answered By |
|----------|-------------|
| Where is price likely headed? | Structure |
| Where is that move starting from? | Narrative |
| When is the highest probability for that move? | Narrative |
| What is the logic behind it? | Narrative |

##### Two Main Concepts for Narrative

| Concept | What It Does |
|---------|--------------|
| **Dealing Ranges** | Identifies price position in current expansion leg → premium or discount |
| **Key Levels** | Refines starting point and ending point of a move |

> **"Narrative transforms directional idea into a proper and feasible directional bias for the day."**

#### Three Potential Outcomes of Directional Bias Layer
1. Know which time frames to use
2. Understand what structure the market is moving in
3. Build a successful narrative (origin + destination + draw liquidity)

---

### Layer 2: Context Layer

This is where your directional bias meets real market behavior. The objective: figure out whether it's the right time to trade or not.

> **"This layer filters out the noise. It adjusts your position to the current market conditions."**

#### Three Core Components

| Component | Description |
|-----------|-------------|
| **1. Time Frame** | The intermediate time frame (4H only) |
| **2. Market Context** | Identify proper key levels + candle ranges within a dealing range |
| **3. Market Conditions** | Assess time of day, time of week, macro news events |

> **"This is the most important time frame because within this you'll build a proper market context AND assess whether market conditions give your entry model a proper technical edge."**

#### Market Context (Trade Idea is Born)

| Element | Description |
|---------|-------------|
| **Dealing Range** | Proper and relevant dealing range |
| **Key Level** | Proper key level relative to dealing range |
| **Candle Range** | A candle range |

> **"Directional bias gives you the WHERE. But context gives you the HOW."**

> **"A strong market context has three essential components: a proper dealing range, a proper key level, and a candle range."**

> **"Without a proper market context even the strongest thesis becomes useless."**

#### Market Conditions (Final Filter)

> **"You could have the best directional bias or the most perfect market context, but if you're not trading within the correct market conditions, you're still going to lose."**

| Condition | What to Check |
|-----------|---------------|
| **Time of Day** | Are we in a key time or kill zone? High probability time window? |
| **Time of Week** | Have we already had our weekly range expansion? TGIF profile? |
| **Macro/News Events** | Filter out NFP, CPI, FOMC - price unstable, models break |

> **"Market conditions is what tells you whether your technical edge is active or not."**

#### Context Layer Outcome

- **Is it now the right time to engage?**
- **Is the market in a condition that favors my entry model?**

> **"Get this layer right and you filter out 90% of the losing trades."**

---

### Layer 3: Execution Layer

This is where the rubber meets the road. Everything built so far comes together and is put to the test.

#### Three Components
1. **Time Frame** - Define the time frame for execution
2. **Entry Trigger** - What triggers the entry
3. **Entry Model** - The specific entry pattern

> **"This layer is the hardest because it demands more than just technical knowledge. This is where your psychological side shows up."**

> **"Most traders don't fail at determining a bias or identifying a context. They fail right here in execution."**

---

### Complete Framework Flow

```
1. DIRECTIONAL BIAS LAYER (Monthly → Weekly → Daily)
   ├── Time Frames: Monthly, Weekly, Daily
   ├── Structure: Quarterly Framework + Seasonal Tendencies + Liquidity/Structure/Profiles
   └── Narrative: Dealing Ranges + Key Levels → origin + destination

2. CONTEXT LAYER (4H)
   ├── Time Frame: 4H only
   ├── Market Context: Dealing Range + Key Level + Candle Range
   └── Market Conditions: Time of Day + Time of Week + News Events

3. EXECUTION LAYER (15min)
   ├── Time Frame: 15min
   ├── Entry Trigger
   └── Entry Model
```

#### Example Flow (from transcript):
- **Daily**: Structure bullish, narrative says retrace to origin (key level), then expand higher
- **4H Tuesday**: Identify where Tuesday's range expansion originates from (retrace to premium key level first?)
- **4H**: Check market conditions - no major news? Reacted at key time? Worth trading based on weekly profile?
- **15min**: If all aligned → execute

> **"If you get this right, you filter out 90% of the losing trades."**

---

## SpeculatorFL - Chapter 03: Step by Step Procedural Framework

> **Source:** SpeculatorFL - Chapter 03: Step by Step Procedural Framework - ICT and CRT

### Directional Bias Layer Procedural Framework

This layer has two active components:
1. **Structural Component** - Build a directional idea
2. **Narrative Component** - Refine directional idea into a directional bias

---

#### Step 1: Build Directional Idea (Structure)

**Step 1A: Establish Macro Directional Hypothesis**
- Use **Quarterly Framework**: Map past quarterly trends, ask if trend continues or reversal expected
- Use **Seasonal Tendencies**: Look at seasonal charts, ask "how does this asset behave in this month?"
- Combine both to build a **directional hypothesis** (not a bias yet)

> **"This isn't going to be based on price action but rather based on time-based behavioral patterns."**

**Step 1B: Test Macro Hypothesis with Structure**
- Use **Market Structure** + **Liquidity Metrics** to validate/invalidate hypothesis
- Apply core principles: measure key highs/lows, see if price breaks above highs/rejects below lows
- Overlay with liquidity metrics to support or challenge directional idea

> **"Structure matters more than the macro directional context."**

| Alignment | Outcome |
|-----------|---------|
| Macro hypothesis **aligned** with structure | More conviction in analysis |
| Macro hypothesis **not aligned** with structure | Give priority to structure, be more cautious |

**Step 1C: Refine with Market Profiles**
- Use market profiles to refine directional idea into specific phases/profiles/cycles
- Protects from trading inside manipulation profile before expansion starts
- Helps avoid entering too early during ranging profiles
- Helps avoid chasing price after expansion profile already played out

> **"By the end of these three steps, you will have a directional idea that's not just based on guesswork, but built on real-time logic."**

---

#### Step 2: Build Directional Bias (Narrative)

**Step 2A: Define Active Dealing Range**
- Identify the most recent and relevant expansion swing
- Define that expansion swing into a dealing range
- Ask: Where is price sitting within that range? Premium or discount?
- Has it moved out of a previous dealing range into a new one?

> **"This gives us a positional context regarding price action."**

**Step 2B: Identify Appropriate Key Levels**
- Identify appropriate key levels within that dealing range
- Identify which key level price would use as a catalyst for expansion move towards drawn liquidity
- Look for specific key level with proper logic behind it, not every order block/FVG

> **"We are looking for a key level that makes the most sense for price to react off of."**

**Step 2C: Connect Origin to Destination**
- Connect the origin (where move begins) to destination (draw liquidity)
- Draw liquidity could be external range liquidity OR key levels within dealing range

> **"That's your narrative. That's your directional bias. That's the storyline you're going to be trading for the day or for the week."**

---

#### Three Critical Questions (Answered by Narrative)

| Question | Description |
|----------|-------------|
| **What direction are we trading in?** | Bullish or bearish |
| **Where is that move most likely to begin?** | The origin (key level in discount) |
| **Where is it most likely to end?** | The destination (draw liquidity) |

---

### Context Layer Procedural Framework

This layer is more straightforward. It has one active component: **Outlining** - defining current market context through dealing range and key levels on 4H.

> **"Narrative is used for building a directional bias on higher time frames. This contextual layer only deals with the intermediate time frame where we will actually find key levels for framing trades."**

#### Step-by-Step for Context Layer

**Step 1: Define Active Dealing Range**
- Must be aligned with higher time frame directional bias
- If HTF bias is bearish → find bearish dealing range (not random or bullish)
- If HTF bias is bullish → find bullish dealing range

**Step 2: Identify Appropriate Key Level + CRT**
- Look for key levels in premium and discount regions
- Identify which key level + which candle range/CRT price could use to react
- Could be pre-formed OR wait for it to form

**Step 3: Wait Patiently for Price to Approach Key Level**
- After defining dealing range, key level, and CRT → wait for price to approach
- Most traders fail here: they jump in instead of waiting

> **"What they struggle with is patience. They jump in because price is moving... and that leads to unnecessary losses."**

---

### Live Example (Monday Trade)

| Step | What Happened |
|------|---------------|
| **HTF Directional Bias** | Bullish, expect price to rebalance dealing range and reach premium key level |
| **4H Dealing Range** | Defined most recent expansion swing (bullish) |
| **4H Key Level** | Identified discount order block (propulsion block) |
| **4H Candle Range** | Candle that closed just above order block |
| **Wait for Price** | Wait for London open (key time), price approached key level |
| **Execution** | During London open, price purged below candle range low, tested discount key level, then expanded higher |

> **"This is exactly how you build a proper market context."**

---

## SpeculatorFL - Live Trade Breakdown: $8,842 in 2 Trades

> **Source:** SpeculatorFL - How I Made $8,842 Day Trading in 2 TRADES

### Weekly Overview

| Day | Directional Bias | Trade Action | Result |
|-----|-----------------|--------------|--------|
| **Monday** | Bullish (SMT divergence) | No trade - no valid market context | Risk off |
| **Tuesday** | Bullish | No trade - ranged all day, no valid context | Risk off |
| **Wednesday** | Bullish → CPI | No trade - CPI day | Risk off |
| **Thursday** | Bearish (adjusted after Wednesday) | Trade executed | Win |
| **Friday** | Bearish (continuation) | Trade executed | Win |

**Total: $8,842 profit, 2 winning trades**

---

### Key Insight: Don't Marry Your Bias

> **"The market is not static. It is constantly evolving. We are constantly responding to new information."**

#### How the Narrative Changed

| Day | What Happened | Bias Adjustment |
|-----|---------------|-----------------|
| **Monday** | SMT divergence with Euro futures → bullish bias | Established bullish |
| **Monday** | Got bullish price action but no market context | Stayed risk off |
| **Tuesday** | Ranged, no retracement, no valid context | Stayed bullish, risk off |
| **Wednesday** | CPI day - monitored passively | Maintained bullish |
| **Wednesday** | Price closed deep in discount region (below OT) | Started reconsidering |
| **Thursday** | Bearish SMT divergence with GU confirmed | **Changed to bearish** |

> **"The narrative that you may have built on Monday may not necessarily remain valid by Wednesday or Thursday."**

---

### Recognizing When to Change Bias

#### Factor 1: Price Closing Deep in Discount Region

| Bullish Environment | Bearish Signal |
|--------------------|----------------|
| Price reacts from discount region | Price closes deep inside discount |
| Price might wick in briefly | Price closes below OT level |
| Rarely closes below OT | Major sign: dealing range not respected |

> **"When you see price closing that deeply inside this discount region, it's a major sign that the dealing range is not being respected."**

#### Factor 2: SMT Divergence Confirmation

- Monday: Bullish SMT (Euro futures already broke lows, EU hadn't)
- Thursday: Bearish SMT (GU took out highs, EU failed) → confirmed bearish bias

#### Factor 3: Recognizing Retracement vs Expansion

| Mistake Made | Lesson Learned |
|--------------|----------------|
| Categorized Monday's move as expansion | It was a **short-term retracement profile** |
| Expected bullish continuation | Price was rebalancing higher time frame dealing range |

> **"I failed to recognize that this bullish price action might have been just a retracement profile on the higher time frame rather than a true expansion."**

---

### Trade Execution (Thursday)

#### Setup
- **Directional Bias**: Bearish
- **Draw Liquidity**: This major low
- **Market Context**: FVG as key level + 1am 4H candle as CRT
- **Sequence**: KOD (price near liquidity, expanding directly from discount without rebalancing)

#### Why Trade from Discount in KOD?
> **"In a KOD sequence, price often expands directly from a discount key level without needing to rebalance the entire dealing range."**

#### Entry Refinement (Avoiding False Entry)

| Initial Entry | Why Avoided | Refined Entry |
|--------------|-------------|---------------|
| First purge of CRT | Order block looked weak | Waited for strong closure |
| Closure wasn't decisive | Not structurally strong | Price had 2nd punch, then closed below 2 consecutive candles |
| | | Entry at low of order block |

> **"I wanted to see a stronger closure below this candle... The closure wasn't decisive."**

#### Key Lesson on Valid Losses

> **"A valid trade can lose and at the same time an invalid trade can win. The outcome of a single trade does not determine whether the decision was correct or not."**

| Truth About Losses | Explanation |
|--------------------|-------------|
| Even best trades can lose | Mathematical inevitability |
| Valid trade losing ≠ mistake | Followed framework perfectly |
| Your edge manifests over time | Through statistical distribution of wins AND losses |
| Profitability comes from | Executing valid setups consistently over large sample |

> **"Your trading edge can only truly manifest itself over time through a statistical distribution of not only wins but also losses."**

---

### Trade Execution (Friday)

| Element | Description |
|---------|-------------|
| **Directional Bias** | Still bearish |
| **Draw Liquidity** | Major low |
| **Context** | Expansion swing as dealing range |
| **Key Level** | Fair value gap (premium) |
| **CRT** | 5pm candle |
| **Execution** | 15min, after dealing range rebalanced, waited for entry confirmation |

---

### Important Framework Rules

1. **Not Every Day is Tradeable**
   - Wait for valid conditions
   - Only 1-2 trades per week is fine
   - Can wait until end of week

2. **Process > Outcome**
   - Focus on executing framework consistently
   - Don't try to predict each trade's outcome
   - Accept valid losses as part of system

3. **Adaptability is Key**
   - Be willing to change narrative when market gives new information
   - Don't become emotionally attached to bias
   - Market communicates - listen objectively

> **"Trading is all about decision making under uncertainty... Your job is to respond intelligently and vigilantly to the new price action."**

---

## Open Questions / Doubts - CLARIFIED

### From MadoCRT (Now with Answers Found in Documentation)

1. ~~FVG Detection Logic~~ - **PARTIALLY DONE**
   - Three-candle imbalances that price fills
   - Model-1 + FVG = highest probability setup
   - KOD + FVG = highest probability combo
   - Fills when price rebalances the gap

2. ~~PO3 (Power of 3) Details~~ - **PARTIALLY DONE** (from SpeculatorFL)
   - Narrows 4 profiles down to 3: Ranging → Manipulation → Expansion
   - Each has own sequence logic and likely outcomes
   - Used for understanding market phase

3. ~~Kill Zone Exact Timing on LTF~~ - **DONE**
   - London: 2:00 AM - 5:00 AM (UTC-5)
   - NY: 7:00 AM - 10:00 AM (UTC-5)
   - Only execute within kill zones
   - Ignore setups outside (lower probability)
   - Behavior: London often establishes direction, NY has high volatility

4. ~~4H Profile Methodology~~ - **DONE**
   - Four profiles: Ranging, Expansion, Retracement, Reversal
   - Power of Three: Ranging → Manipulation → Expansion
   - Use to filter which conditions to trade
   - Don't trade inside manipulation profile before expansion starts

5. ~~Time Theory Details~~ - **DONE** (from RomeoTPT)
   - Monday: Often fake high
   - Tuesday: Real high forms
   - Thursday/Friday: Often opposite end of range forms
   - Always align with time theory

6. ~~SMT Divergence Handling~~ - **DONE** (confirmation process: Model-1 + MSS)

7. ~~News Event Handling~~ - **DONE**
   - Filter out: NFP, CPI, FOMC
   - Price becomes unstable during these events
   - Models tend to break
   - Stay risk-off on high-impact news days

8. ~~Dealings Ranges~~ - **DONE**
   - Definition: Most recent expansion swing defined as a range
   - Price position: Premium (upper) or Discount (lower)
   - Must align with HTF directional bias
   - Trade: Define range → identify key levels → connect origin to destination

9. ~~Order Block Identification Criteria~~ - **DONE**
   - Institutional order zones from previous strong directional candles
   - Propulsion block: Formed by testing a previous order block
   - Key: Must have clear, decisive closure (not weak/ambiguous)
   - Visual strength matters

10. ~~Advanced CRT Patterns~~ - **DONE** (covered in documentation)
    - Three Candle CRT (core model)
    - Two Candle CRT (purge + distribute in one candle)
    - Multiple Candle CRT: Inside Bar and Outside Bar variants
    - TSQ sequence covers all phases

---

### From RomeoTPT (Now with Answers Found in Documentation)

1. ~~Market Profile Understanding~~ - **DONE**
2. ~~Million DOOLF FVG Model~~ - **DONE** (Model-1 + FVG = highest probability)
3. ~~FVG Detection Logic~~ - **PARTIALLY DONE** (see MadoCRT section)
4. ~~Time Theory Details~~ - **DONE** (weekly timing)
5. ~~Specific Timing Patterns~~ - **DONE** (range vs trend behavior)
6. ~~Daily/Weekly Open Specifics~~ - **DONE** (Monday midnight, Sunday 5PM NY)
7. ~~Algorithm Timing Details~~ - **DONE** (NY time based)
8. ~~Reverse Engineering Trades~~ - **DONE** (recording + journaling)
   - Highest level: Record trades and watch candles minute by minute
   - Journal every win, loss, and miss
   - Analyze what happened before, during, and after
9. ~~Failure Swing Details~~ - **DONE**
10. ~~Candle Thickness/Strength~~ - **DONE**
11. ~~Entry 2 and 3 Details~~ - **DONE**
12. ~~Sound Logic Sequence of Entries~~ - **DONE**
13. ~~When to Avoid Entry 2~~ - **DONE**
14. ~~Draw Liquidity Priority~~ - **DONE**
15. ~~SMT Details~~ - **DONE**
16. ~~KOD Detailed Rules~~ - **DONE**
17. ~~KOD Location~~ - **DONE**

---

## Pending from MadoCRT

- [x] Entry timing (confirmation approach) - DONE
- [x] Stop loss placement rules - DONE (protected swing)
- [x] Take profit targets (50%, opposite end of range, 1:2 R:R) - DONE
- [x] Lower timeframe methodology - DONE
- [x] Timeframe alignment rules (HTF/ITF/LTF) - DONE
- [x] Kill zones - DONE
- [x] HTF bias rules - DONE
- [x] Order flow identification - DONE
- [x] Model 1 entry details - DONE
- [x] TSQ sequence (all phases) - DONE
- [x] OTE/Fibonacci retracement rules (60-75%) - DONE
- [x] Breaker block identification - DONE
- [x] Kiss of Death (KOD) - DONE
- [x] OHLC/OLHC candle logic - DONE
- [x] Close confirmation rule - DONE
- [x] Breaker + OTE combination (highest probability) - DONE
- [x] Turtle soup mechanics (market maker perspective) - DONE (RomeoTPT)
- [x] CRT definition and fractal nature - DONE (RomeoTPT)
- [x] Candle 1-2-3 sequence - DONE (RomeoTPT)
- [x] 50% target rule - DONE (RomeoTPT)
- [x] Sell above/below open rule - DONE (RomeoTPT)
- [x] Bias rules (close vs wick) - DONE (RomeoTPT)
- [x] Model-1 complete rules - DONE (RomeoTPT CRT Secrets EP 1)
- [x] Thick candle criteria - DONE (RomeoTPT)
- [x] Time theory (weekly timing) - DONE (RomeoTPT)
- [x] FVG enhancement for Model-1 - DONE (RomeoTPT)
- [ ] FVG detection logic - PENDING
- [ ] PO3 concept details - PENDING
- [ ] SMT divergence handling - PENDING
- [ ] News event handling - PENDING
- [ ] Dealings ranges - PENDING
- [ ] Advanced CRT patterns - PENDING