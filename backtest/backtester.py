"""
Backtester for CRT Trading Bot.
Runs strategy on historical data and calculates performance metrics.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.crt_strategy import CRTStrategyImpl
from risk.risk_manager import RiskManager
from data.data_fetcher import DataFetcher
from data.forex_loader import ForexDataLoader
from config import config


class Backtester:
    """CRT Strategy Backtester."""

    def __init__(
        self,
        initial_capital: float = 10_000,
        risk_per_trade: float = 0.03,
        use_kill_zone: bool = False,
        use_market_profile: bool = False,
        use_time_theory: bool = False,
        use_kod: bool = True,
        use_model1: bool = True,
        use_ote: bool = True,
        use_breaker_block: bool = True,
        use_candle3_only: bool = True,
        use_true_mss: bool = True,
        timezone_offset: int = 0,
        stop_mode: str = "independent",
        use_ltf_execution: bool = False,
        ltf_window_hours: int = 4,
        retest_window: int = 4,
        max_leverage: float = 3.0,
        entry_mode: str = "immediate",
        entry_logic: str = "extreme",
        transaction_cost: float = 10.0,
        fee_rate: float = 0.0,
    ):
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.stop_mode = stop_mode
        self.use_ltf_execution = use_ltf_execution
        self.ltf_window_hours = ltf_window_hours
        self.retest_window = retest_window
        self.max_leverage = max_leverage
        self.entry_mode = entry_mode
        self.entry_logic = entry_logic
        self.transaction_cost = transaction_cost
        self.fee_rate = fee_rate

        self.strategy = CRTStrategyImpl(
            use_kill_zone=use_kill_zone,
            use_market_profile=use_market_profile,
            use_time_theory=use_time_theory,
            use_kod=use_kod,
            use_model1=use_model1,
            use_ote=use_ote,
            use_breaker_block=use_breaker_block,
            use_candle3_only=use_candle3_only,
            use_true_mss=use_true_mss,
            timezone_offset=timezone_offset,
        )
        self.risk_manager = RiskManager(
            capital=initial_capital,
            risk_per_trade=risk_per_trade
        )

        self.trades = []
        self.equity_curve = [initial_capital]
        self.daily_returns = []
        self.positions: List[Dict] = []
        self.pending_signals: List[Dict] = []
        self.pending_orders: List[Dict] = []
        self.pending_ltf_orders: List[Dict] = []
        self.missed_orders: List[Dict] = []

    def _compute_cost(self, size: float, price: float) -> float:
        """Total cost: fixed + percentage of notional."""
        return self.transaction_cost + size * price * self.fee_rate

    def run(
        self,
        df: pd.DataFrame,
        symbol: str,
        stop_loss_pct: float = 0.02,
        take_profit_ratios: List[float] = [1.5, 2.0],
        ltf_df: pd.DataFrame = None,
    ) -> Dict:
        if self.entry_mode in ("ltf", "ltf_limit", "immediate_ltf"):
            df = self.strategy.generate_signals(df, ltf_df=None)
        else:
            df = self.strategy.generate_signals(df, ltf_df=ltf_df)
        self.positions = []
        self.pending_signals = []
        self.pending_orders = []
        self.pending_ltf_orders = []
        self.missed_orders = []

        for i in range(len(df)):
            row = df.iloc[i]
            signal = row["signal"]
            current_price = row["close"]

            # Step 1: Manage exits for existing positions (always runs)
            self._update_trailing_stops(df, i, current_price)
            self._check_exits(df, i, current_price, take_profit_ratios)

            # Step 2: Check pending limit orders for fill
            if self.entry_mode == "limit_retest":
                self._check_limit_retest_fill(df, i)
            elif self.entry_mode in ("ltf", "ltf_limit") and ltf_df is not None:
                self._check_ltf_fill(df, i, ltf_df)
                if self.entry_mode == "ltf_limit":
                    self._check_ltf_limit_fill(df, i, ltf_df)
            else:
                # Legacy pending Model-1 retest (immediate mode)
                # Legacy pending Model-1 retest (immediate mode)
                for pending in list(self.pending_signals):
                    retested = self._check_model1_retest(df, i, pending)
                    if retested:
                        self._open_trade_from_pending(pending, i, df, symbol, stop_loss_pct)
                        self.pending_signals.remove(pending)
                    elif self._pending_expired(pending, i):
                        self.pending_signals.remove(pending)

            # Step 3: Handle new signals
            if signal == 0:
                continue

            direction = "long" if signal == 1 else "short"
            range_id = int(row.get("crt_range_id", 0))
            inv_price = row.get("crt_inv_price")
            stop_price = row.get("crt_stop_price")
            phase_type = row.get("crt_phase_type", "unknown")

            # Extract CRT entry level (the rule-based limit price)
            crt_entry = None
            if inv_price is not None and isinstance(inv_price, (int, float)) and not np.isnan(inv_price):
                crt_entry = float(inv_price)

            if self.entry_mode == "immediate":
                # Legacy Mode-1 retest or immediate entry
                if phase_type == "Model-1" and self.retest_window > 0 and crt_entry is not None:
                    self.pending_signals.append({
                        "entry_level": crt_entry,
                        "direction": direction,
                        "signal_idx": i,
                        "phase": phase_type,
                        "range_id": range_id,
                        "stop_price": stop_price,
                        "inv_price": inv_price,
                        "symbol": symbol,
                    })
                    continue
                entry_price = crt_entry if crt_entry is not None else current_price
                self._create_trade(df, i, df.index[i], entry_price, direction, range_id,
                                   phase_type, stop_price, inv_price, symbol, stop_loss_pct)
                self.pending_signals = [p for p in self.pending_signals if p.get("range_id") != range_id]

            elif self.entry_mode == "limit_retest":
                extreme = crt_entry if crt_entry is not None else current_price
                close_price = current_price

                # Model-1: place limit order, wait for retest (future candles)
                if phase_type == "Model-1":
                    if self.entry_logic == "conservative":
                        fill_levels = [close_price, extreme]
                    else:
                        fill_levels = [extreme]
                    self.pending_orders.append({
                        "entry_level": extreme,
                        "fill_levels": fill_levels,
                        "direction": direction,
                        "signal_idx": i,
                        "phase": phase_type,
                        "range_id": range_id,
                        "stop_price": stop_price,
                        "inv_price": inv_price,
                        "symbol": symbol,
                        "stop_loss_pct": stop_loss_pct,
                    })
                else:
                    # Breaker/KOD/BB/OTE: these ARE the retest — enter at their extreme
                    if self.entry_logic == "conservative":
                        fill_levels = [close_price, extreme]
                    else:
                        fill_levels = [extreme]
                    self._check_immediate_fill(df, i, fill_levels, direction, range_id,
                                               phase_type, stop_price, inv_price, symbol,
                                               stop_loss_pct)

            elif self.entry_mode == "ltf" and ltf_df is not None:
                close_time = df.index[i] + pd.Timedelta(hours=4)
                self.pending_ltf_orders.append({
                    "direction": direction,
                    "inv_price": inv_price,
                    "stop_price": stop_price,
                    "range_id": range_id,
                    "phase": phase_type,
                    "symbol": symbol,
                    "signal_close_time": close_time,
                    "signal_idx": i,
                    "stop_loss_pct": stop_loss_pct,
                })

            elif self.entry_mode == "ltf_limit" and ltf_df is not None:
                self.pending_orders.append({
                    "entry_level": inv_price if inv_price is not None and not (isinstance(inv_price, float) and np.isnan(inv_price)) else current_price,
                    "direction": direction,
                    "signal_idx": i,
                    "signal_time": df.index[i],
                    "phase": phase_type,
                    "range_id": range_id,
                    "stop_price": stop_price,
                    "inv_price": inv_price,
                    "symbol": symbol,
                    "stop_loss_pct": stop_loss_pct,
                    "ltf_df": ltf_df,
                })

            elif self.entry_mode == "ltf" and ltf_df is None:
                # Fallback: no LTF data, enter immediately
                entry_price = crt_entry if crt_entry is not None else current_price
                self._create_trade(df, i, df.index[i], entry_price, direction, range_id,
                                   phase_type, stop_price, inv_price, symbol, stop_loss_pct)

        for pos in list(self.positions):
            if pos["status"] == "open":
                final_price = df.iloc[-1]["close"]
                pnl = self._calculate_pnl(pos["direction"], pos["entry_price"], final_price, pos["position_size"])
                self._close_trade(pos, df.index[-1], final_price, pnl, "EOD")

        # Expire any remaining pending LTF orders
        for order in list(self.pending_ltf_orders):
            self.missed_orders.append({
                "symbol": order["symbol"],
                "entry_level": order["inv_price"],
                "direction": order["direction"],
                "signal_idx": order["signal_idx"],
                "phase": order["phase"],
                "range_id": order["range_id"],
                "reason": "eod_expired",
            })

        results = self._calculate_metrics()
        results["trade_log"] = pd.DataFrame(self.trades) if self.trades else pd.DataFrame()
        results["missed_orders"] = len(self.missed_orders)
        if self.missed_orders:
            results["missed_orders_df"] = pd.DataFrame(self.missed_orders)
        return results

    def _resolve_ltf_entry(self, signal_time, inv_price, direction, ltf_df, window_hours=None):
        """Look ahead in 15m data for confirmation entry after a 4H signal.

        Rules:
        - 4H candles are timestamped at OPEN time. Signal is known at CLOSE time.
        - Start search from 4H close time (signal_time + 4h) to avoid lookahead bias.
        - Skip the 15m candle at close_time (it just opened, not yet closed).
        - Confirmation: 15m candle close crosses crt_inv_price in the trade direction.
        - Returns (entry_time, entry_price) or (None, None) if not confirmed within window.
        """
        if window_hours is None:
            window_hours = self.ltf_window_hours
        if inv_price is None or (isinstance(inv_price, float) and np.isnan(inv_price)):
            return None, None
        inv_price = float(inv_price)
        close_time = signal_time + pd.Timedelta(hours=4)
        window_end = close_time + pd.Timedelta(hours=window_hours)
        try:
            ltf_window = ltf_df.loc[close_time:window_end]
        except KeyError:
            return None, None
        if len(ltf_window) == 0:
            return None, None
        # Skip first 15m candle: it opens at close_time, hasn't closed yet in live trading
        first_ts = ltf_window.index[0]
        if isinstance(first_ts, pd.Timestamp) and first_ts == close_time:
            ltf_window = ltf_window.iloc[1:]
        if len(ltf_window) == 0:
            return None, None
        if direction == "long":
            for idx in range(len(ltf_window)):
                close = ltf_window.iloc[idx]["close"]
                if close > inv_price:
                    return ltf_window.index[idx], close
        else:
            for idx in range(len(ltf_window)):
                close = ltf_window.iloc[idx]["close"]
                if close < inv_price:
                    return ltf_window.index[idx], close
        return None, None

    def save_trade_log(self, path):
        """Export trade log to CSV."""
        if not self.trades:
            return
        df = pd.DataFrame(self.trades)
        cols = ["symbol", "entry_time", "exit_time", "direction", "entry_price", "exit_price",
                "stop_loss", "position_size", "pnl", "exit_reason", "phase",
                "range_id", "partial_exited", "original_risk", "inv_price", "stop_price"]
        cols = [c for c in cols if c in df.columns]
        df[cols].to_csv(path, index=False)

    def _create_trade(self, df, idx, entry_time, entry_price, direction, range_id,
                      phase_type, stop_price, inv_price, symbol, stop_loss_pct):
        """Open a trade at the given entry price and time.

        Rules:
        - Size on initial_capital (no compounding) for realistic PnL
        - If a position already exists for this range_id: scale in at 50% size
          and adjust SL to the new signal's level if better
        """
        sl = self._compute_stop_loss(entry_price, direction, stop_price, stop_loss_pct)
        risk = abs(entry_price - sl)
        if risk <= 0:
            return

        existing = [p for p in self.positions if p.get("range_id") == range_id and p["status"] == "open"]

        if existing:
            pos = existing[0]
            if direction == "long":
                if sl > pos["stop_loss"]:
                    pos["stop_loss"] = sl
                base_size = (self.initial_capital * self.risk_per_trade) / pos.get("original_risk", risk)
                add_size = base_size * 0.5
                pos["position_size"] += add_size
                pos["phase"] = f"{pos['phase']}+{phase_type}"
            else:
                if sl < pos["stop_loss"]:
                    pos["stop_loss"] = sl
                base_size = (self.initial_capital * self.risk_per_trade) / pos.get("original_risk", risk)
                add_size = base_size * 0.5
                pos["position_size"] += add_size
                pos["phase"] = f"{pos['phase']}+{phase_type}"
            max_notional = self.initial_capital * self.max_leverage
            if pos["position_size"] * pos["entry_price"] > max_notional:
                pos["position_size"] = max_notional / pos["entry_price"]
            return

        position_size = (self.initial_capital * self.risk_per_trade) / risk
        notional = position_size * entry_price
        max_notional = self.initial_capital * self.max_leverage
        if notional > max_notional:
            position_size = max_notional / entry_price
        trade = {
            "symbol": symbol, "signal_time": df.index[idx], "entry_time": entry_time,
            "entry_price": entry_price,
            "direction": direction, "position_size": position_size, "stop_loss": sl,
            "original_sl": sl, "original_risk": risk, "partial_exited": False,
            "status": "open", "range_id": range_id, "phase": phase_type,
            "inv_price": inv_price if inv_price is not None else None,
            "stop_price": stop_price if stop_price is not None else None,
        }
        self.positions.append(trade)

    def _check_immediate_fill(self, df, idx, fill_levels, direction, range_id,
                              phase_type, stop_price, inv_price, symbol, stop_loss_pct):
        """Check if the current candle's wick touches any fill level and fill immediately.
        Used for Breaker/KOD/BB signals where the signal candle IS the retest.
        After fill, removes any pending limit orders for the same range_id
        to prevent duplicate positions (Bug 1 fix).
        """
        row = df.iloc[idx]
        for level in fill_levels:
            if (direction == "long" and row["low"] <= level) or \
               (direction == "short" and row["high"] >= level):
                self._create_trade(df, idx, df.index[idx], level, direction, range_id,
                                    phase_type, stop_price, inv_price, symbol, stop_loss_pct)
                self.pending_orders = [o for o in self.pending_orders if o.get("range_id") != range_id]
                return

    def _compute_stop_loss(self, entry_price, direction, stop_price, fallback_pct):
        """Compute SL: use crt_stop_price if valid, else fixed %."""
        if stop_price is not None and isinstance(stop_price, (int, float)) and not np.isnan(stop_price):
            s = float(stop_price)
            if direction == "long" and s < entry_price:
                return s
            elif direction == "short" and s > entry_price:
                return s
        if direction == "long":
            return entry_price * (1 - fallback_pct)
        else:
            return entry_price * (1 + fallback_pct)

    def _check_model1_retest(self, df, idx, pending):
        """Check if price retested the Model-1 entry level at candle idx.
        
        For longs: retest when low <= entry_level (price touched our limit)
        For shorts: retest when high >= entry_level
        """
        row = df.iloc[idx]
        level = pending["entry_level"]
        if pending["direction"] == "long":
            return row["low"] <= level
        else:
            return row["high"] >= level

    def _pending_expired(self, pending, current_idx):
        """Check if a pending signal has expired after retest_window candles."""
        if self.retest_window <= 0:
            return False
        return (current_idx - pending["signal_idx"]) > self.retest_window

    def _open_trade_from_pending(self, pending, retest_idx, df, symbol, stop_loss_pct):
        """Open a trade when a Model-1 pending signal is retested."""
        entry_price = pending["entry_level"]
        entry_time = df.index[retest_idx]
        self._create_trade(
            df, retest_idx, entry_time, entry_price,
            pending["direction"], pending["range_id"],
            pending["phase"], pending["stop_price"],
            pending["inv_price"], symbol, stop_loss_pct,
        )

    def _check_limit_retest_fill(self, df, idx):
        """Check all pending limit orders for fill on 4H candle wick.
        Fill levels checked in order (close first for conservative, extreme only for base rule).
        Expire after retest_window candles (0 = never expire).
        """
        for order in list(self.pending_orders):
            row = df.iloc[idx]
            level = None
            filled = False

            for test_level in order["fill_levels"]:
                if order["direction"] == "long" and row["low"] <= test_level:
                    level = test_level
                    filled = True
                    break
                elif order["direction"] == "short" and row["high"] >= test_level:
                    level = test_level
                    filled = True
                    break

            if filled:
                if any(pos.get("range_id") == order["range_id"] and pos["status"] == "open" for pos in self.positions):
                    self.pending_orders.remove(order)
                    continue
                self._create_trade(
                    df, idx, df.index[idx], level,
                    order["direction"], order["range_id"],
                    order["phase"], order["stop_price"],
                    order["inv_price"], order["symbol"],
                    order["stop_loss_pct"],
                )
                self.pending_orders.remove(order)
            elif self.retest_window > 0 and (idx - order["signal_idx"]) > self.retest_window:
                self.missed_orders.append({
                    "symbol": order["symbol"], "entry_level": order["entry_level"],
                    "direction": order["direction"], "signal_idx": order["signal_idx"],
                    "phase": order["phase"], "range_id": order["range_id"],
                    "reason": "expired",
                })
                self.pending_orders.remove(order)

    def _check_ltf_limit_fill(self, df, idx, ltf_df):
        """Check pending LTF limit orders: fill when 15M wick touches inv_price within window.
        Looks at 15M data within the current 4H candle's time range.
        """
        if idx >= len(df):
            return
        candle_time = df.index[idx]
        candle_end = candle_time + pd.Timedelta(hours=4)
        signal_direction = df.iloc[idx].get("signal", 0)

        for order in list(self.pending_orders):
            if (idx - order["signal_idx"]) > max(self.retest_window, self.ltf_window_hours // 4) and self.retest_window > 0:
                self.missed_orders.append({
                    "symbol": order["symbol"], "entry_level": order["entry_level"],
                    "direction": order["direction"], "signal_idx": order["signal_idx"],
                    "phase": order["phase"], "range_id": order["range_id"],
                    "reason": "expired",
                })
                self.pending_orders.remove(order)
                continue

            signal_time = order.get("signal_time", candle_time)
            window_end = signal_time + pd.Timedelta(hours=self.ltf_window_hours)
            if candle_time > window_end:
                continue

            try:
                ltf_window = ltf_df.loc[candle_time:candle_end]
            except KeyError:
                ltf_window = ltf_df.loc[candle_time:]

            if len(ltf_window) == 0:
                continue

            level = order["entry_level"]
            filled = False
            if order["direction"] == "long":
                for j in range(len(ltf_window)):
                    if ltf_window.iloc[j]["low"] <= level:
                        filled = True
                        break
            else:
                for j in range(len(ltf_window)):
                    if ltf_window.iloc[j]["high"] >= level:
                        filled = True
                        break

            if filled:
                self._create_trade(
                    df, idx, candle_time, level,
                    order["direction"], order["range_id"],
                    order["phase"], order["stop_price"],
                    order["inv_price"], order["symbol"],
                    order["stop_loss_pct"],
                )
                self.pending_orders.remove(order)

    @staticmethod
    def _calc_body_pct(candle) -> float:
        """Calculate body percentage of a candle."""
        rng = float(candle["high"]) - float(candle["low"])
        if rng <= 0:
            return 0
        body = abs(float(candle["close"]) - float(candle["open"]))
        return body / rng

    def _detect_ltf_model1(self, ltf_data, direction, inv_price):
        """Detect a proper Model-1 setup on 15M data per CRT rules.

        Rules 861-867 (adapted to LTF):
        1. Find a THICK candle (body >= 70%) that purges inv_price area
        2. Next candle must close OPPOSITE direction (confirmation)
        3. Entry at the purge candle's extreme (low for long, high for short)
        4. Wait for price to RETEST the entry level → fill

        Rule 1199: "Find Model-1 on LTF for entry" (for KOD)

        Returns (entry_time, entry_price) or None.
        """
        inv_price = float(inv_price)
        for i in range(len(ltf_data) - 1):
            c = ltf_data.iloc[i]
            if self._calc_body_pct(c) < 0.7:
                continue
            next_c = ltf_data.iloc[i + 1]
            if direction == "long":
                if c["close"] < c["open"] and c["low"] <= inv_price * 1.005:
                    if next_c["close"] > c["high"]:
                        entry = c["low"]
                        for j in range(i + 2, len(ltf_data)):
                            if ltf_data.iloc[j]["low"] <= entry:
                                return ltf_data.index[j], entry
            else:
                if c["close"] > c["open"] and c["high"] >= inv_price * 0.995:
                    if next_c["close"] < c["low"]:
                        entry = c["high"]
                        for j in range(i + 2, len(ltf_data)):
                            if ltf_data.iloc[j]["high"] >= entry:
                                return ltf_data.index[j], entry
        return None

    def _check_ltf_fill(self, df, idx, ltf_df):
        """Check pending LTF orders: confirm when 15M close crosses inv_price within window.
        Called each 4H candle iteration, scans 15M data within the current 4H candle's range.
        Expires orders past the ltf_window_hours window from signal's 4H close time.

        Rules:
        - 4H candles use OPEN timestamps. Signal is known at CLOSE time (signal_open + 4h).
        - The 15M candle at close_time - 15m closes CONCURRENTLY with the 4H candle.
          It must be checked in the first iteration (candle_time == close_time).
        - 15M candles at close_time and later haven't closed yet — skip them.
        """
        if ltf_df is None:
            return
        candle_time = df.index[idx]
        candle_end = candle_time + pd.Timedelta(hours=4)

        for order in list(self.pending_ltf_orders):
            close_time = order["signal_close_time"]
            window_end = close_time + pd.Timedelta(hours=self.ltf_window_hours)

            # Expire if this 4H candle opens past the LTF window
            if candle_time >= window_end:
                self.missed_orders.append({
                    "symbol": order["symbol"],
                    "entry_level": order["inv_price"],
                    "direction": order["direction"],
                    "signal_idx": order["signal_idx"],
                    "phase": order["phase"],
                    "range_id": order["range_id"],
                    "reason": "ltf_window_expired",
                })
                self.pending_ltf_orders.remove(order)
                continue

            inv_price = float(order["inv_price"])
            filled = False
            entry_time = None
            entry_price = None

            # Step A: On the first check (candle_time == close_time), also check the
            # 15M candle that closes concurrently with the 4H (timestamped close_time - 15m).
            if candle_time == close_time:
                concurrent_ts = close_time - pd.Timedelta(minutes=15)
                try:
                    concurrent = ltf_df.loc[concurrent_ts]
                except (KeyError, TypeError):
                    concurrent = None
                if concurrent is not None:
                    if order["direction"] == "long" and concurrent["close"] > inv_price:
                        filled = True
                        entry_time = close_time
                        entry_price = concurrent["close"]
                    elif order["direction"] == "short" and concurrent["close"] < inv_price:
                        filled = True
                        entry_time = close_time
                        entry_price = concurrent["close"]

            # Step B: Search forward in 15M data from the later of (close_time, candle_time)
            if not filled:
                scan_start = max(close_time, candle_time)
                try:
                    ltf_slice = ltf_df.loc[scan_start:candle_end]
                except KeyError:
                    ltf_slice = ltf_df.loc[scan_start:]

                if len(ltf_slice) > 0:
                    # Skip the 15M candle at scan_start if it equals close_time (hasn't closed yet)
                    first_ts = ltf_slice.index[0]
                    if isinstance(first_ts, pd.Timestamp) and first_ts == scan_start and scan_start == close_time:
                        ltf_slice = ltf_slice.iloc[1:]

                    if len(ltf_slice) > 0:
                        # Phase-specific LTF criteria per CRT rules
                        if order["phase"] == "KOD":
                            # Rule 1199: "Find Model-1 on LTF for entry"
                            m1 = self._detect_ltf_model1(ltf_slice, order["direction"], inv_price)
                            if m1 is not None:
                                filled = True
                                entry_time = m1[0]
                                entry_price = m1[1]
                        else:
                            # M1/Breaker/BB/OTE: 15m close crossing inv_price (general LTF execution per Rule 674)
                            if order["direction"] == "long":
                                for j in range(len(ltf_slice)):
                                    close = ltf_slice.iloc[j]["close"]
                                    if close > inv_price:
                                        filled = True
                                        entry_time = ltf_slice.index[j]
                                        entry_price = close
                                        break
                            else:
                                for j in range(len(ltf_slice)):
                                    close = ltf_slice.iloc[j]["close"]
                                    if close < inv_price:
                                        filled = True
                                        entry_time = ltf_slice.index[j]
                                        entry_price = close
                                        break

            if filled:
                self._create_trade(
                    df, idx, entry_time, entry_price,
                    order["direction"], order["range_id"],
                    order["phase"], order["stop_price"],
                    order["inv_price"], order["symbol"],
                    order["stop_loss_pct"],
                )
                self.pending_ltf_orders.remove(order)

    def _update_trailing_stops(self, df, idx: int, current_price: float):
        if self.stop_mode != "tsq_trail" or idx >= len(df):
            return
        row = df.iloc[idx]
        signal = row["signal"]
        if signal == 0:
            return
        new_range_id = int(row.get("crt_range_id", 0))
        if new_range_id == 0:
            return
        stop_price = row.get("crt_stop_price")
        if stop_price is None or (isinstance(stop_price, float) and np.isnan(stop_price)):
            return

        signal_direction = int(signal)
        if signal_direction == 0:
            return

        for pos in self.positions:
            if pos["status"] != "open":
                continue
            if pos.get("range_id", 0) == new_range_id and pos.get("entry_time") < df.index[idx]:
                if (pos["direction"] == "long" and signal_direction != 1) or \
                   (pos["direction"] == "short" and signal_direction != -1):
                    continue
                new_sl = float(stop_price)
                if pos["direction"] == "long":
                    if new_sl > pos["stop_loss"]:
                        pos["stop_loss"] = new_sl
                else:
                    if new_sl < pos["stop_loss"]:
                        pos["stop_loss"] = new_sl

    def _check_exits(self, df, idx: int, current_price: float, tp_ratios: List[float]):
        for pos in list(self.positions):
            if pos["status"] != "open":
                continue

            risk = pos.get("original_risk", abs(pos["entry_price"] - pos["stop_loss"]))
            if pos["direction"] == "long":
                profit_points = current_price - pos["entry_price"]
                sl_hit = current_price <= pos["stop_loss"]
            else:
                profit_points = pos["entry_price"] - current_price
                sl_hit = current_price >= pos["stop_loss"]

            if sl_hit:
                pnl = self._calculate_pnl(pos["direction"], pos["entry_price"], pos["stop_loss"], pos["position_size"])
                self._close_trade(pos, df.index[idx], pos["stop_loss"], pnl, "SL")
                continue

            tp1 = self._calculate_take_profit(pos["entry_price"], pos["original_sl"], pos["direction"], tp_ratios[0])
            tp_hit = (pos["direction"] == "long" and current_price >= tp1) or \
                     (pos["direction"] == "short" and current_price <= tp1)

            if tp_hit:
                if not pos.get("partial_exited", False):
                    half_size = pos["position_size"] * 0.5
                    pnl_partial = self._calculate_pnl(pos["direction"], pos["entry_price"], tp1, half_size)
                    exit_cost = self._compute_cost(half_size, tp1)
                    pnl_partial -= exit_cost
                    partial = pos.copy()
                    partial.update({"exit_time": df.index[idx], "exit_price": tp1, "pnl": pnl_partial,
                                    "exit_reason": "TP1_50%", "position_size": half_size, "status": "closed",
                                    "cost": exit_cost})
                    self.trades.append(partial)
                    self.risk_manager.update_capital(pnl_partial)
                    self.equity_curve.append(self.risk_manager.capital)

                    pos["position_size"] = half_size
                    pos["stop_loss"] = pos["entry_price"]
                    pos["partial_exited"] = True

                if len(tp_ratios) > 1:
                    tp2 = self._calculate_take_profit(pos["entry_price"], pos.get("original_sl", pos["stop_loss"]),
                                                      pos["direction"], tp_ratios[1])
                    tp2_hit = (pos["direction"] == "long" and current_price >= tp2) or \
                              (pos["direction"] == "short" and current_price <= tp2)
                    if tp2_hit:
                        pnl_full = self._calculate_pnl(pos["direction"], pos["entry_price"], tp2, pos["position_size"])
                        self._close_trade(pos, df.index[idx], tp2, pnl_full, "TP2")

    def _calculate_pnl(self, direction: str, entry: float, exit: float, size: float) -> float:
        """Calculate PnL for a trade."""
        if direction == "long":
            return (exit - entry) * size
        else:
            return (entry - exit) * size

    def _calculate_take_profit(
        self,
        entry: float,
        sl: float,
        direction: str,
        rr_ratio: float
    ) -> float:
        """Calculate take profit price based on R:R ratio."""
        risk = abs(entry - sl)
        reward = risk * rr_ratio

        if direction == "long":
            return entry + reward
        else:
            return entry - reward

    def _close_trade(
        self,
        trade: Dict,
        exit_time: pd.Timestamp,
        exit_price: float,
        pnl: float,
        exit_reason: str
    ):
        """Close a trade and record results, deducting entry + exit costs."""
        entry_cost = self._compute_cost(trade["position_size"], trade["entry_price"])
        exit_cost = self._compute_cost(trade["position_size"], exit_price)
        cost = entry_cost + exit_cost
        net_pnl = pnl - cost
        trade["exit_time"] = exit_time
        trade["exit_price"] = exit_price
        trade["pnl"] = net_pnl
        trade["cost"] = cost
        trade["exit_reason"] = exit_reason
        trade["status"] = "closed"

        self.trades.append(trade)
        self.risk_manager.update_capital(net_pnl)
        self.equity_curve.append(self.risk_manager.capital)

    def _calculate_metrics(self) -> Dict:
        """Calculate backtest performance metrics."""
        if not self.trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "profit_factor": 0,
                "max_drawdown": 0,
                "sharpe_ratio": 0,
            }

        trades_df = pd.DataFrame(self.trades)

        # Basic metrics
        wins = [t for t in self.trades if t["pnl"] > 0]
        losses = [t for t in self.trades if t["pnl"] <= 0]

        total_pnl = sum(t["pnl"] for t in self.trades)
        win_rate = len(wins) / len(self.trades) if self.trades else 0

        # Profit factor
        gross_profit = sum(t["pnl"] for t in wins) if wins else 0
        gross_loss = abs(sum(t["pnl"] for t in losses)) if losses else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Drawdown
        equity = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdowns = (equity - running_max) / running_max
        max_drawdown = abs(drawdowns.min())

        # Sharpe ratio (simplified)
        returns = np.diff(equity) / equity[:-1]
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 1 and returns.std() > 0 else 0

        # Average trade metrics
        avg_win = np.mean([t["pnl"] for t in wins]) if wins else 0
        avg_loss = np.mean([t["pnl"] for t in losses]) if losses else 0

        return {
            "total_trades": len(self.trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": win_rate * 100,
            "total_pnl": total_pnl,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown * 100,
            "sharpe_ratio": sharpe_ratio,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "avg_trade": total_pnl / len(self.trades) if self.trades else 0,
        }

    def print_results(self, symbol: str):
        """Print backtest results."""
        metrics = self._calculate_metrics()

        print(f"\n{'='*50}")
        print(f"Backtest Results - {symbol}")
        print(f"{'='*50}")
        print(f"Total Trades:     {metrics['total_trades']}")
        print(f"Winning Trades:  {metrics['winning_trades']}")
        print(f"Losing Trades:   {metrics['losing_trades']}")
        print(f"Win Rate:        {metrics['win_rate']:.1f}%")
        print(f"Total PnL:       ${metrics['total_pnl']:.2f}")
        print(f"Profit Factor:   {metrics['profit_factor']:.2f}")
        print(f"Max Drawdown:    {metrics['max_drawdown']:.1f}%")
        print(f"Sharpe Ratio:    {metrics['sharpe_ratio']:.2f}")
        print(f"Avg Win:         ${metrics['avg_win']:.2f}")
        print(f"Avg Loss:        ${metrics['avg_loss']:.2f}")
        print(f"{'='*50}\n")

    def get_trades_df(self) -> pd.DataFrame:
        """Get trades as DataFrame."""
        return pd.DataFrame(self.trades)


def run_backtest_for_pair(
    symbol: str,
    timeframe: str = "4h",
    start_date: str = "2025-01-01",
    end_date: str = "2026-01-01",
    use_ltf: bool = False,
    ltf_timeframe: str = "15m",
) -> Dict:
    """Run backtest for a single trading pair.

    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Main timeframe (default 4h)
        start_date: Start date for data
        end_date: End date for data
        use_ltf: Whether to use LTF confirmation
        ltf_timeframe: LTF timeframe (default 15m)
    """

    # Fetch data
    fetcher = DataFetcher()
    since = int(pd.Timestamp(start_date).timestamp() * 1000)

    try:
        df = fetcher.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        print(f"Loaded {len(df)} candles for {symbol}")
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return {}

    # Fetch LTF data if enabled
    ltf_df = None
    if use_ltf:
        try:
            ltf_df = fetcher.fetch_ohlcv(symbol, ltf_timeframe, since=since, limit=4000)
            print(f"Loaded {len(ltf_df)} candles for LTF ({ltf_timeframe})")
        except Exception as e:
            print(f"Warning: Could not fetch LTF data: {e}")

    # Run backtest
    backtester = Backtester(
        initial_capital=config.INITIAL_CAPITAL,
        risk_per_trade=config.RISK_PER_TRADE
    )

    results = backtester.run(df, symbol, ltf_df=ltf_df)
    backtester.print_results(symbol)

    return results


if __name__ == "__main__":
    # Test with sample data first
    print("Running backtest test with sample data...")

    # Create sample data
    np.random.seed(42)
    dates = pd.date_range(start="2025-01-01", periods=500, freq="4h")

    prices = []
    price = 50000
    for i in range(500):
        # Simulate CRT-like moves
        if i % 20 < 10:  # Uptrend phase
            price += np.random.randn() * 500 + 50
        else:  # Downtrend phase
            price += np.random.randn() * 500 - 50
        prices.append(price)

    df = pd.DataFrame({
        'open': prices,
        'high': [p + abs(np.random.randn() * 300) for p in prices],
        'low': [p - abs(np.random.randn() * 300) for p in prices],
        'close': [p + np.random.randn() * 200 for p in prices],
        'volume': np.random.randint(1000, 10000, 500),
    }, index=dates)

    # Run backtest
    backtester = Backtester(initial_capital=10_000, risk_per_trade=0.03)
    results = backtester.run(df, "TEST/USDT")
    backtester.print_results("TEST/USDT")

    print("Test completed!")