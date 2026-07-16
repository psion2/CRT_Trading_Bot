# CRT v2 Indicator — Refinement & Deviation Log

> Purpose: track every design choice/refinement by its SOURCE, so we can decide
> at the **end of the project** whether to keep the ones that are NOT grounded in
> RULES.md. Nothing in section A/B is implemented unless explicitly agreed.

Legend: 🟡 = based on Claude's own CRT knowledge (decide at end) · 🔧 = engineering
choice · ✅ = grounded in RULES.md.

---

## A. Refinements based on Claude's CRT knowledge (NOT explicit in RULES.md)
**Decision deferred to the very end.**

1. **Breaker zone from candle BODY** instead of full high–low range (tighter zone,
   tighter stop). RULES.md only says "the last opposite-colour candle." 🟡
2. **"Displace-away" guard** — require price to move a minimum distance away from
   the breaker zone before a retest counts (prevents a `BRK` firing 1 bar after
   Model-1). RULES.md implies displacement→retest but gives no distance rule. 🟡
3. **Rejection-close on breaker retest** — require the retest candle to CLOSE back
   out of the zone, not just wick-touch it. Extends the RULES "closes confirm"
   principle, but RULES.md does not state it for the breaker retest specifically.
   (Evidence: 09:00 Jul-2 `BRK` fired on a touch, then price blew through.) 🟡
4. **Cosmetic** — trim the breaker box at the retest bar; marker/label spacing. 🟡

---

## B. Engineering choices / interpretations (structural, not from rules)

1. Turtle soup detected on the **chart (LTF)** against the **HTF range** (execution
   view), rather than requiring the HTF candle's own close to confirm. 🔧
2. **One active setup per side** at a time (no overlapping same-side setups). 🔧
3. Setup lifetime = **`m1Window` bars** (default 24) — a bar-count approximation of
   "the setup lives into Candle 3." 🔧
4. **Single-candle** turtle soup only (RULES.md also describes a 2-candle variant —
   not yet implemented). 🔧
5. **OTE (Phase 5) displacement leg** = protected swing (0%) → the extreme price
   reaches after Model-1 (100%). The 100% anchor auto-extends while price makes new
   highs/lows, then freezes when it stalls. RULES.md defines the 60-75% zone but not
   the exact leg anchors — this is the structural interpretation. 🔧
6. **OTE entry price = zone midpoint (~67.5%)**. RULES.md calls OTE "range-based, not
   an exact level" (luring liquidity), so a single fill line is a convenience; the box
   shows the true 60-75% zone. 🔧
7. **OTE armed by the Model-1 signal** (same trigger as the breaker), not gated behind
   the breaker retest. Matches RULES.md "breaker + OTE combine at the same zone." 🔧
8. **KOD internal liquidity = confirmed pivots** (`ta.pivothigh/low`, default len 3).
   RULES.md says KOD sweeps "engineered liquidity / old high-low" but doesn't define
   which swing — pivots are the structural proxy. 🔧
9. **One KOD per sequence.** RULES.md calls KOD "the LAST turtle soup before target,"
   which is only knowable in hindsight; we fire the first qualifying counter-target
   sweep after Model-1 and suppress the rest to avoid clutter. 🔧
10. **KOD "50% bounce" handled implicitly** — the KOD is a *counter-target* sweep, so
    its geometry already places it at a retracement extreme; we don't separately gate
    on a measured 50% bounce. Optional discount/premium-half filter is provided. 🔧
11. **Bias source = a SEPARATE, HIGHER bias timeframe** (`biasTF`, default Daily `D`),
    NOT the 4H CRT-range candle. RULES.md "Three Time Frame Structure" (lines 1863 /
    2019): bias = Daily/Weekly, dealing range/CRT = 4H, execution = 15m — bias must
    carry higher authority than the range. **Revised 2026-07-10**: the earlier
    self-contained "read bias off the CRT candle itself" simplification was the
    false-hope source (a bullish 4H range sitting inside a bearish Daily still
    green-lit longs) and is retired. ✅ grounded (was the deferred upgrade → now done).
12. **Bias applied at the Model-1 (bias-at-inception).** The gate masks m1LongSig/
    m1ShortSig once; breaker/OTE/KOD inherit it because they all arm off those. A
    setup armed under a valid bias plays out even if a later HTF close flips the bias
    mid-sequence (the thesis is set at Model-1). 🔧
13. **Neutral bias (inside candle / both-sides pierced with equal closes) allows BOTH
    sides**; turtle-soup markers are also bias-gated (chart cleanliness). **No
    premium/discount location gate** — user chose direction-only (Jul-2026); "buy
    discount / sell premium" stays a deferred add-on. 🔧
14. **Kill-zone gate = ENTRY-TIME, applied per-entry independently** (Phase 7b, user's
    choice Jul-2026). Unlike bias (gated once at Model-1 inception, cascades), the time
    filter masks each entry marker (M1 / Breaker / OTE / KOD) by ITS OWN bar's session,
    NOT the Model-1's. Rationale: RULES.md LTF step 1 is "Time Check: Must be within kill
    zone" at *execution*, so a breaker retest at 07:30 is a valid NY entry even if its M1
    formed at 06:00 outside the zone. Implementation: brk/OTE/KOD signals are display-only
    so they're masked at source (`:= kzOk`); m1LongSig/m1ShortSig are dual-use (drive the
    cascade) so only their DISPLAY sites are masked, never the signal. 🔧
15. **KOD event still recorded when outside a kill zone** — `kodFired := true` fires
    unconditionally; only the marker (`kodLongSig/kodShortSig := kzOk`) is suppressed.
    RULES.md: exactly one KOD per sequence ("it's never not there"); an out-of-KZ KOD is
    still THE KOD (untradeable), so we don't leave the sequence open to mismark a later
    sweep. 🔧
16. **Turtle-soup markers are NOT kill-zone gated** — TS is the manipulation/setup
    signal, not an entry, and RULES.md gates *entries* ("no entries outside kill zones").
    TS stays visible as context. (Bias still gates TS; that's a cleanliness choice, B13.) 🔧
17. **Kill-zone windows anchored to `America/New_York`** (default), not a fixed UTC
    offset. RULES.md gives "UTC-5 or UTC-4" + "algorithm functions on NY time"; the IANA
    zone applies the correct EST/EDT offset automatically so the windows never drift with
    US daylight saving, regardless of the chart's own timezone. Day filter pinned to all
    7 days (`:1234567`) since this is a 24/7 crypto perp. 🔧
18. **Bias = STRUCTURAL read of the bias candle vs the previous one** (added 2026-07-10),
    replacing the single close-vs-close. A priority ladder on the last closed `biasTF`
    candle (`bc1/bh1/bl1`) vs the prior one (`bc2/bh2/bl2`):
    1. **Close BEYOND** prior high/low → break → continuation (close>prevHigh = bull,
       close<prevLow = bear).
    2. Else **wick beyond** prior high/low but **close back inside** → rejection / HTF
       turtle soup → reversal (wicked above only = bear, wicked below only = bull).
    3. Else (inside, or **both** sides pierced) → mild close-vs-close lean.
    The three signals are ✅ RULES.md — close-vs-prev (332/782), wick-above→lower /
    wick-below→higher (334-335/787), close-beyond = structural break (778-780/1610/1915),
    and MadoCRT's HTF "candle shape" read (1283/1600). The **priority ORDERING**
    (close-break > wick-reject > close-lean, i.e. "closes confirm" outranks "wicks lie")
    and the **both-sides-pierced → close-lean** tiebreak are my synthesis. 🔧 (built on
    ✅ components). Deferred richer bias still open: order-flow via key highs/lows
    (1876-1924), draw-on-liquidity / premium-discount, daily-open sell-above/buy-below
    (352-356), 2-3 candle accumulation-manipulation-distribution shape.

---

## C. Deferred items that ARE grounded in RULES.md (planned / optional)

- ✅ **HTF bias filter** (Phase 7a) — DONE, **revised 2026-07-10**. Now a STRUCTURAL
  read (break / wick-reject / close-lean, B18) on a SEPARATE higher bias timeframe
  (`biasTF`, default Daily, B11) — no longer read off the 4H CRT candle. Interpretations
  in B11-B13 + B18. The *draw-on-liquidity* reading of bias (last-swept side /
  premium-discount) and order-flow-by-structure remain deferred refinements.
- ✅ **Kill zones + time theory** (Phase 7b) — DONE. London 02:00-05:00 + NY 07:00-10:00
  (NY time); entry-time gate per B14. Deferred: Asian range & London-Close windows (🟡
  my-knowledge, see §A note), Thu/Fri "bet the house" time-of-week emphasis.
- ✅ **Thick threshold 0.70** — RULES says "thick" = 0.70 (currently default 0.50)
- ✅ **FVG confluence** for Model-1 — "Model-1 + FVG = highest probability"
- ✅ **Key-level confluence** — "CRT near order blocks / FVG / swings"
- ✅ **50% + opposite-end targets** — minimum + full target
- ✅ **OTE zone** (Phase 5) — DONE (60-75% fib retrace of the Model-1 displacement)
- ✅ **KOD** (Phase 6) — DONE (final counter-target sweep of internal liquidity)
- ✅ **Breaker + OTE confluence highlight** — "same zone = highest probability"
  (RULES.md). Both are drawn now; a dedicated "highest-probability" marker when the
  breaker zone and OTE zone OVERLAP is a planned enhancement.
- ✅ **OTE requirements gate** — RULES.md lists "clear HTF bias" as a requirement;
  now satisfied by the Phase 7a bias filter (OTE arms off the bias-gated Model-1).
- ✅ **KOD + FVG confluence** — RULES.md: "Bearish FVG + KOD above old high = high-prob
  SELL / Bullish FVG + KOD below old low = BUY." Needs FVG detection (not yet built).
- ✅ **KOD warning (close beyond wick)** — RULES.md: "you don't want them to go above a
  KOD." Currently the KOD wick is just the SL; a distinct "KOD failed / SMT warning"
  flag when price closes back through it is a planned enhancement.
- ✅ **2-candle turtle soup** variant

---

## Change history
- Phase 3: Model-1 entry switched from MadoCRT (confirmation-candle) to RomeoTPT
  (purge-candle) model, per user preference. Both are in RULES.md.
- Phase 3: setup decoupled from HTF boundary (persists into Candle 3); SL = protected
  swing (deepest wick, extended through W-shaped reactions). ✅ grounded in RULES.
- Phase 5: OTE added. 60-75% fib retracement zone of the Model-1 displacement leg;
  SL = protected swing, target = CRT high/low. All ✅ grounded in RULES.md ("Phase 4:
  OTE", RomeoTPT EP7). Interpretations logged in B5-B7 above.
- Phase 5: OTE/breaker colors split (OTE = solid-bordered blue/purple, breaker =
  soft-filled teal/maroon) + optional numeric debug label. Cosmetic. 🔧
- Phase 6: KOD added. Final counter-target sweep of internal-liquidity pivots inside
  the Model-1→target window; SL beyond the KOD wick, target = CRT level. ✅ grounded in
  RULES.md ("Kiss of Death", RomeoTPT EP2). Interpretations in B8-B10 above.
- Phase 7a: HTF bias filter added. Direction gate from the CRT-timeframe close vs. its
  previous close (RULES.md "Bias Rules": close above = bullish/longs, below =
  bearish/shorts). Applied at the Model-1 so breaker/OTE/KOD inherit it; TS markers
  gated too; faint bg tint shows the bias. Toggle `useBias`. ✅ grounded; interpretations
  in B11-B13. Chosen: CRT-TF source + direction-only (no premium/discount). Deferred:
  separate higher bias TF, premium/discount location gate. Kill-zone/time filters =
  Phase 7b (pending).
- Phase 7b: Kill-zone / time-of-day filter added. London 02:00-05:00 + NY 07:00-10:00,
  anchored to America/New_York (RULES.md "Kill Zones"; "algorithm functions on NY time").
  Entry-time gate: each entry (M1/Breaker/OTE/KOD) masked by its own bar's session; the
  sequence still forms outside. TS left ungated (setup context, not an entry). ✅ grounded;
  interpretations in B14-B17. Inputs: `useKZ` (master, default ON), `useKZlon`/`useKZny`
  (per-session), `kzTZ` (timezone), `showKZbg` (blue shading). Corner HUD now shows bias
  (row 0) + live kill-zone status (row 1). Deferred: Asian & London-Close windows,
  Thu/Fri time-of-week emphasis.
- Phase 7a REVISION (2026-07-10): bias was on the wrong timeframe AND too crude. Fixed
  both. (a) **Timeframe** — added a separate `biasTF` input (default Daily), so bias is
  read from a higher authority than the 4H CRT range, per RULES.md "Three Time Frame
  Structure" (bias=Daily/Weekly, range=4H, exec=15m). The old "bias off the CRT candle
  itself" was the false-hope source. (b) **Method** — replaced single close-vs-close with
  a STRUCTURAL read of the bias candle vs the previous one (break → continuation / wick-
  reject → reversal / else close-lean), matching MadoCRT's HTF candle-shape bias. Trimmed
  the range `request.security` to `[h1,l1,t1]` (old `o1/c1/c2` were bias-only). HUD now
  shows the bias TF. ✅ grounded; interpretations B11 (rev), B13 (rev), B18 (new).
  Awaiting chart re-verification.
- Phase 3 REVISION (2026-07-16): wick-vs-body Model-1 entry added (RULES.md "When to
  Use Wick vs Body for Entry", MadoCRT EP-2). Previously entry was ALWAYS the purge
  candle's wick extreme, and confirmation ALWAYS required a close beyond that wick —
  the missing body tier was why entries looked "late" (e.g. EURUSD 15m 05-Jun: 3h of
  chop between body low and wick low never confirmed until the 18:00 dump). Now:
  (a) trigger relaxed to a thick close beyond the purge BODY edge; (b) entry level =
  wick extreme if the close is beyond the wick, else the body edge. Body edge is
  COLOR-INDEPENDENT — long: max(open,close) = body high; short: min(open,close) =
  body low. RULES.md says "Entry at Open (body)", but a literal open is wrong on a
  green long-purge / red short-purge candle (open sits on the far side of the body);
  user-confirmed the body-high/body-low generalization is the intended rule. New state:
  shortPurgeBodyLow / longPurgeBodyHigh, tracked alongside the wick refs everywhere
  the purge candle moves. SL unchanged (protected swing). ✅ grounded in RULES.md.
  Awaiting chart re-verification (both tiers: body-zone close → body entry; wick
  break close → wick entry).
