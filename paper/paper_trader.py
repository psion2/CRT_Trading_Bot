"""
Paper Trader for CRT Trading Bot.
Real-time paper trading using CCXT exchange data.
Supports all 3 entry modes: immediate, limit_retest, ltf (experimental).
"""

import time
import json
import logging
import urllib.request
import urllib.error
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategies.crt_strategy import CRTStrategyImpl
from risk.risk_manager import RiskManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "paper_trader.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


class PaperTrader:
    """Paper trading engine running on real-time exchange data.

    Polls CCXT every 60s, detects new 4h/15m candle closes,
    generates CRT signals, manages orders, logs to CSV + Telegram.
    """

    def __init__(
        self,
        exchange_id: str = "binance",
        symbol: str = "BTC/USDT",
        entry_mode: str = "limit_retest",
        use_ltf: bool = False,
        initial_capital: float = 10_000,
        risk_per_trade: float = 0.02,
        max_leverage: float = 3.0,
        transaction_cost: float = 10.0,
        retest_window: int = 4,
        ltf_window_hours: int = 18,
        stop_loss_pct: float = 0.02,
        tp_ratios: Optional[list] = None,
        entry_logic: str = "extreme",
        fee_rate: float = 0.0,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        trade_log_path: Optional[str] = None,
        state_path: Optional[str] = None,
    ):
        self.exchange_id = exchange_id
        self.symbol = symbol
        self.entry_mode = entry_mode
        self.use_ltf = use_ltf
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.max_leverage = max_leverage
        self.transaction_cost = transaction_cost
        self.fee_rate = fee_rate
        self.retest_window = retest_window
        self.ltf_window_hours = ltf_window_hours
        self.stop_loss_pct = stop_loss_pct
        self.tp_ratios = tp_ratios or [1.5, 2.0]
        self.entry_logic = entry_logic
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id

        base_dir = Path(__file__).parent
        self.trade_log_path = trade_log_path or str(base_dir / "trade_log.csv")
        self.state_path = state_path or str(base_dir / "trader_state.json")

        self.strategy = CRTStrategyImpl(
            use_kod=True, use_model1=True, use_ote=True,
            use_breaker_block=True, use_candle3_only=True, use_true_mss=True,
        )
        self.risk_manager = RiskManager(capital=initial_capital, risk_per_trade=risk_per_trade)

        self.exchange = None
        self._init_exchange()

        self.df_4h = pd.DataFrame()
        self.df_15m = pd.DataFrame()
        self.last_4h_ts: Optional[pd.Timestamp] = None
        self.last_15m_ts: Optional[pd.Timestamp] = None
        self.processed_signal_indices: set = set()

        self.positions: List[Dict] = []
        self.pending_signals: List[Dict] = []
        self.pending_orders: List[Dict] = []
        self.pending_ltf_orders: List[Dict] = []
        self.trades: List[Dict] = []
        self.missed_orders: List[Dict] = []
        self.equity_curve: List[float] = [initial_capital]
        self.running = False

        self._write_csv_header()

    def _init_exchange(self):
        """Initialize CCXT exchange."""
        try:
            import ccxt
            exchange_map = {
                "binance": ccxt.binance,
                "hyperliquid": ccxt.hyperliquid,
            }
            if self.exchange_id in exchange_map:
                self.exchange = exchange_map[self.exchange_id]({
                    "enableRateLimit": True,
                })
            else:
                self.exchange = getattr(ccxt, self.exchange_id)({"enableRateLimit": True})
            self.exchange.load_markets()
            log.info(f"Connected to {self.exchange_id}")
        except Exception as e:
            log.error(f"Failed to init exchange {self.exchange_id}: {e}")
            raise

    def _fetch_ohlcv(self, timeframe: str, limit: int = 200) -> pd.DataFrame:
        """Fetch OHLCV data from exchange and return as DataFrame."""
        try:
            raw = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
            df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            return df
        except Exception as e:
            log.warning(f"fetch_ohlcv ({timeframe}) failed: {e}")
            return pd.DataFrame()

    def _detect_new_candle(self, df_new: pd.DataFrame, df_old: pd.DataFrame) -> Optional[pd.Timestamp]:
        """Return the timestamp of the newest row in df_new not present in df_old."""
        if df_new.empty:
            return None
        if df_old.empty:
            return df_new.index[-1]
        new_ts = df_new.index[-1]
        old_ts = df_old.index[-1] if not df_old.empty else None
        if old_ts is None or new_ts > old_ts:
            return new_ts
        return None

    def _is_new_4h_candle(self, df_new: pd.DataFrame) -> bool:
        """Check if a new 4h candle has closed since last check."""
        ts = self._detect_new_candle(df_new, self.df_4h)
        if ts is not None:
            return True
        return False

    def _is_new_15m_candle(self, df_new: pd.DataFrame) -> bool:
        """Check if a new 15m candle has closed since last check."""
        ts = self._detect_new_candle(df_new, self.df_15m)
        if ts is not None:
            return True
        return False

    def _process_4h_candle(self):
        """Handle a new 4h candle: re-run strategy and check for new signals."""
        df = self.strategy.generate_signals(self.df_4h, ltf_df=None)
        new_signal_idx = df.index[-1]
        if new_signal_idx in self.processed_signal_indices:
            return
        row = df.loc[new_signal_idx]
        signal = row.get("signal", 0)
        if signal == 0:
            self.processed_signal_indices.add(new_signal_idx)
            return
        direction = "long" if signal == 1 else "short"
        self._handle_signal(df, new_signal_idx, row, direction)
        self.processed_signal_indices.add(new_signal_idx)

    def _handle_signal(self, df, idx, row, direction):
        """Route a new signal to the appropriate entry mode handler."""
        range_id = int(row.get("crt_range_id", 0))
        inv_price = row.get("crt_inv_price")
        stop_price = row.get("crt_stop_price")
        phase_type = row.get("crt_phase_type", "unknown")
        current_price = row["close"]
        crt_entry = float(inv_price) if inv_price is not None and isinstance(inv_price, (int, float)) and not np.isnan(inv_price) else None

        msg = f"SIGNAL {direction.upper()} {phase_type} range={range_id} inv=${crt_entry:,.0f} price=${current_price:,.0f}"
        log.info(msg)
        self._notify(msg)

        if self.entry_mode == "immediate":
            if phase_type == "Model-1" and self.retest_window > 0 and crt_entry is not None:
                self.pending_signals.append({
                    "entry_level": crt_entry,
                    "direction": direction,
                    "signal_idx": idx,
                    "signal_time": idx,
                    "phase": phase_type,
                    "range_id": range_id,
                    "stop_price": stop_price,
                    "inv_price": inv_price,
                    "symbol": self.symbol,
                })
                log.info(f"  M1 pending limit at ${crt_entry:,.0f}")
                return
            self._open_trade(crt_entry or current_price, direction, range_id, phase_type, stop_price, inv_price, signal_time=idx)

        elif self.entry_mode == "limit_retest":
            extreme = crt_entry if crt_entry is not None else current_price
            close_price = current_price
            if phase_type == "Model-1":
                fill_levels = [close_price, extreme] if self.entry_logic == "conservative" else [extreme]
                self.pending_orders.append({
                    "entry_level": extreme,
                    "fill_levels": fill_levels,
                    "direction": direction,
                    "signal_idx": idx,
                    "signal_time": idx,
                    "phase": phase_type,
                    "range_id": range_id,
                    "stop_price": stop_price,
                    "inv_price": inv_price,
                    "symbol": self.symbol,
                    "stop_loss_pct": self.stop_loss_pct,
                })
                log.info(f"  M1 pending limit at ${extreme:,.0f}")
            else:
                fill_levels = [close_price, extreme] if self.entry_logic == "conservative" else [extreme]
                for level in fill_levels:
                    if (direction == "long" and row["low"] <= level) or \
                       (direction == "short" and row["high"] >= level):
                        self._open_trade(level, direction, range_id, phase_type, stop_price, inv_price, signal_time=idx)
                        self.pending_orders = [o for o in self.pending_orders if o.get("range_id") != range_id]
                        break

        elif self.entry_mode == "ltf" and self.use_ltf:
            close_time = idx + pd.Timedelta(hours=4)
            self.pending_ltf_orders.append({
                "direction": direction,
                "inv_price": inv_price,
                "stop_price": stop_price,
                "range_id": range_id,
                "phase": phase_type,
                "symbol": self.symbol,
                "signal_close_time": close_time,
                "signal_idx": idx,
                "signal_time": idx,
                "stop_loss_pct": self.stop_loss_pct,
            })
            log.info(f"  LTF pending: waiting for 15m close crossing ${crt_entry:,.0f}")

    def _check_retests(self):
        """Check pending M1 retests (immediate mode legacy)."""
        for pending in list(self.pending_signals):
            if self.df_4h.empty:
                continue
            last = self.df_4h.iloc[-1]
            level = pending["entry_level"]
            retested = (
                (pending["direction"] == "long" and last["low"] <= level) or
                (pending["direction"] == "short" and last["high"] >= level)
            )
            if retested:
                self._open_trade(level, pending["direction"], pending["range_id"],
                                 pending["phase"], pending["stop_price"], pending["inv_price"],
                                 signal_time=pending.get("signal_time"))
                self.pending_signals.remove(pending)
                log.info(f"  M1 retested at ${level:,.0f}: FILLED")
            elif len(self.df_4h) - self.df_4h.index.get_loc(pending["signal_time"]) > self.retest_window:
                self.missed_orders.append(pending)
                self.pending_signals.remove(pending)
                log.info(f"  M1 expired at ${level:,.0f}")

    def _check_limit_orders(self):
        """Check pending limit orders for fill on each 4h candle close."""
        if self.df_4h.empty or self.entry_mode != "limit_retest":
            return
        last = self.df_4h.iloc[-1]
        for order in list(self.pending_orders):
            level = None
            filled = False
            for test_level in order["fill_levels"]:
                if order["direction"] == "long" and last["low"] <= test_level:
                    level = test_level
                    filled = True
                    break
                elif order["direction"] == "short" and last["high"] >= test_level:
                    level = test_level
                    filled = True
                    break
            if filled:
                if any(p.get("range_id") == order["range_id"] and p["status"] == "open" for p in self.positions):
                    self.pending_orders.remove(order)
                    continue
                self._open_trade(level, order["direction"], order["range_id"],
                                 order["phase"], order["stop_price"], order["inv_price"],
                                 signal_time=order.get("signal_time"))
                self.pending_orders.remove(order)
                log.info(f"  Limit order filled at ${level:,.0f}")
            elif self.retest_window > 0 and len(self.df_4h) > 1:
                current_idx = self.df_4h.index.get_loc(self.df_4h.index[-1])
                signal_idx = self.df_4h.index.get_loc(order["signal_idx"]) if order["signal_idx"] in self.df_4h.index else current_idx
                if current_idx - signal_idx > self.retest_window:
                    self.missed_orders.append(order)
                    self.pending_orders.remove(order)
                    log.info(f"  Limit order expired at ${order['entry_level']:,.0f}")

    def _check_ltf_fills(self):
        """Check pending LTF orders on 15m data (matches backtester logic)."""
        if self.df_15m.empty or not self.use_ltf or self.df_4h.empty:
            return
        candle_time = self.df_4h.index[-1]
        candle_end = candle_time + pd.Timedelta(hours=4)
        for order in list(self.pending_ltf_orders):
            close_time = order["signal_close_time"]
            window_end = close_time + pd.Timedelta(hours=self.ltf_window_hours)
            if candle_time >= window_end:
                self.missed_orders.append(order)
                self.pending_ltf_orders.remove(order)
                log.info(f"  LTF order expired: ${order['inv_price']:,.0f}")
                continue
            inv_price = float(order["inv_price"])
            filled = False
            entry_price = None

            # Step A: Check concurrent 15m candle (at close_time - 15m) closing with 4h signal
            if candle_time == close_time:
                concurrent_ts = close_time - pd.Timedelta(minutes=15)
                if concurrent_ts in self.df_15m.index:
                    concurrent = self.df_15m.loc[concurrent_ts]
                    if order["direction"] == "long" and concurrent["close"] > inv_price:
                        filled = True
                        entry_price = concurrent["close"]
                    elif order["direction"] == "short" and concurrent["close"] < inv_price:
                        filled = True
                        entry_price = concurrent["close"]

            # Step B: Scan 15m data from the later of (close_time, candle_time) to candle_end
            if not filled:
                scan_start = max(close_time, candle_time)
                ltf_slice = self.df_15m[self.df_15m.index >= scan_start]
                ltf_slice = ltf_slice[ltf_slice.index <= candle_end] if not ltf_slice.empty else ltf_slice
                if not ltf_slice.empty:
                    if ltf_slice.index[0] == scan_start and scan_start == close_time:
                        ltf_slice = ltf_slice.iloc[1:]
                    if not ltf_slice.empty:
                        if order["phase"] == "KOD":
                            m1 = self._detect_ltf_model1(ltf_slice, order["direction"], inv_price)
                            if m1 is not None:
                                filled = True
                                entry_price = m1[1]
                        else:
                            for j in range(len(ltf_slice)):
                                close = ltf_slice.iloc[j]["close"]
                                if order["direction"] == "long" and close > inv_price:
                                    filled = True
                                    entry_price = close
                                    break
                                elif order["direction"] == "short" and close < inv_price:
                                    filled = True
                                    entry_price = close
                                    break
            if filled and entry_price is not None:
                self._open_trade(entry_price, order["direction"], order["range_id"],
                                 order["phase"], order["stop_price"], order["inv_price"],
                                 signal_time=order.get("signal_time"))
                self.pending_ltf_orders.remove(order)

    def _detect_ltf_model1(self, ltf_data, direction, inv_price):
        """Detect proper Model-1 on 15M data (Rule 1199)."""
        inv_price = float(inv_price)
        for i in range(len(ltf_data) - 1):
            c = ltf_data.iloc[i]
            body = abs(c["close"] - c["open"])
            rng = c["high"] - c["low"]
            if rng <= 0 or body / rng < 0.7:
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

    def _update_trailing_stops(self):
        """Trail stop loss when new same-range signal provides tighter SL."""
        if self.df_4h.empty:
            return
        row = self.df_4h.iloc[-1]
        signal = row.get("signal", 0)
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
            if pos.get("range_id", 0) == new_range_id:
                if (pos["direction"] == "long" and signal_direction != 1) or \
                   (pos["direction"] == "short" and signal_direction != -1):
                    continue
                new_sl = float(stop_price)
                if pos["direction"] == "long" and new_sl > pos["stop_loss"]:
                    pos["stop_loss"] = new_sl
                    log.info(f"  Trail SL: {pos['direction'].upper()} range={new_range_id} SL→${new_sl:,.0f}")
                elif pos["direction"] == "short" and new_sl < pos["stop_loss"]:
                    pos["stop_loss"] = new_sl
                    log.info(f"  Trail SL: {pos['direction'].upper()} range={new_range_id} SL→${new_sl:,.0f}")

    def _compute_sl(self, entry_price, direction, stop_price):
        """Compute stop loss from crt_stop_price or fallback pct."""
        if stop_price is not None and isinstance(stop_price, (int, float)) and not np.isnan(stop_price):
            s = float(stop_price)
            if direction == "long" and s < entry_price:
                return s
            elif direction == "short" and s > entry_price:
                return s
        return entry_price * (1 - self.stop_loss_pct if direction == "long" else 1 + self.stop_loss_pct)

    def _open_trade(self, entry_price, direction, range_id, phase_type, stop_price, inv_price, signal_time=None):
        """Open a new position (with scale-in support)."""
        sl = self._compute_sl(entry_price, direction, stop_price)
        risk = abs(entry_price - sl)
        if risk <= 0:
            return
        existing = [p for p in self.positions if p.get("range_id") == range_id and p["status"] == "open"]
        if existing:
            pos = existing[0]
            base_size = (self.initial_capital * self.risk_per_trade) / pos.get("original_risk", risk)
            add_size = base_size * 0.5
            if direction == "long":
                if sl > pos["stop_loss"]:
                    pos["stop_loss"] = sl
            else:
                if sl < pos["stop_loss"]:
                    pos["stop_loss"] = sl
            pos["position_size"] += add_size
            pos["phase"] = f"{pos['phase']}+{phase_type}"
            max_notional = self.initial_capital * self.max_leverage
            if pos["position_size"] * pos["entry_price"] > max_notional:
                pos["position_size"] = max_notional / pos["entry_price"]
            msg = f"SCALE-IN {direction.upper()} {phase_type} range={range_id} size={add_size:.4f} @ ${entry_price:,.0f}"
            log.info(msg)
            self._notify(msg)
            return
        position_size = (self.initial_capital * self.risk_per_trade) / risk
        notional = position_size * entry_price
        max_notional = self.initial_capital * self.max_leverage
        if notional > max_notional:
            position_size = max_notional / entry_price
        trade = {
            "symbol": self.symbol,
            "signal_time": signal_time,
            "entry_time": datetime.now(),
            "entry_price": entry_price,
            "direction": direction,
            "position_size": position_size,
            "stop_loss": sl,
            "original_sl": sl,
            "original_risk": risk,
            "partial_exited": False,
            "status": "open",
            "range_id": range_id,
            "phase": phase_type,
            "inv_price": inv_price if inv_price is not None else None,
            "stop_price": stop_price if stop_price is not None else None,
        }
        self.positions.append(trade)
        msg = f"ENTRY {direction.upper()} {phase_type} range={range_id} size={position_size:.4f} @ ${entry_price:,.0f} SL=${sl:,.0f}"
        log.info(msg)
        self._notify(msg)

    def _check_positions(self):
        """Check SL/TP for all open positions using latest 4h close."""
        if self.df_4h.empty:
            return
        current_price = self.df_4h.iloc[-1]["close"]
        for pos in list(self.positions):
            if pos["status"] != "open":
                continue
            risk = pos.get("original_risk", abs(pos["entry_price"] - pos["stop_loss"]))
            direction = pos["direction"]
            sl_hit = (direction == "long" and current_price <= pos["stop_loss"]) or \
                     (direction == "short" and current_price >= pos["stop_loss"])
            if sl_hit:
                pnl = self._calc_pnl(direction, pos["entry_price"], pos["stop_loss"], pos["position_size"])
                self._close_trade(pos, current_price, pnl, "SL")
                continue
            tp1 = self._calc_tp(pos["entry_price"], pos["original_sl"], direction, self.tp_ratios[0])
            tp_hit = (direction == "long" and current_price >= tp1) or \
                     (direction == "short" and current_price <= tp1)
            if tp_hit:
                if not pos.get("partial_exited", False):
                    half = pos["position_size"] * 0.5
                    exit_cost = self._compute_cost(half, tp1)
                    pnl_partial = self._calc_pnl(direction, pos["entry_price"], tp1, half) - exit_cost
                    self._record_close(pos, datetime.now(), tp1, pnl_partial, "TP1_50%", half)
                    pos["position_size"] = half
                    pos["stop_loss"] = pos["entry_price"]
                    pos["partial_exited"] = True
                    msg = f"TP1 {direction.upper()} {pos['phase']} range={pos['range_id']} PnL=${pnl_partial:,.2f}"
                    log.info(msg)
                    self._notify(msg)
                if len(self.tp_ratios) > 1:
                    tp2 = self._calc_tp(pos["entry_price"], pos.get("original_sl", pos["stop_loss"]), direction, self.tp_ratios[1])
                    tp2_hit = (direction == "long" and current_price >= tp2) or \
                              (direction == "short" and current_price <= tp2)
                    if tp2_hit:
                        pnl_full = self._calc_pnl(direction, pos["entry_price"], tp2, pos["position_size"])
                        self._close_trade(pos, current_price, pnl_full, "TP2")

    def _close_trade(self, pos, exit_price, pnl, reason):
        """Close a position and record the trade."""
        entry_cost = self._compute_cost(pos["position_size"], pos["entry_price"])
        exit_cost = self._compute_cost(pos["position_size"], exit_price)
        cost = entry_cost + exit_cost
        net_pnl = pnl - cost
        now = datetime.now()
        self._record_close(pos, now, exit_price, net_pnl, reason, pos["position_size"])
        pos["status"] = "closed"
        msg = f"CLOSE {reason} {pos['direction'].upper()} {pos['phase']} PnL=${net_pnl:,.2f} @ ${exit_price:,.0f}"
        log.info(msg)
        self._notify(msg)

    def _record_close(self, pos, exit_time, exit_price, pnl, reason, size):
        """Record a closed trade (full or partial)."""
        trade = {
            "symbol": self.symbol,
            "signal_time": str(pos.get("signal_time", "")),
            "entry_time": str(pos["entry_time"]),
            "exit_time": str(exit_time),
            "direction": pos["direction"],
            "entry_price": pos["entry_price"],
            "exit_price": exit_price,
            "stop_loss": pos["stop_loss"],
            "position_size": size,
            "pnl": pnl,
            "exit_reason": reason,
            "phase": pos["phase"],
            "range_id": pos["range_id"],
            "partial_exited": pos.get("partial_exited", False),
        }
        self.trades.append(trade)
        self._append_csv(trade)
        self.risk_manager.update_capital(pnl)
        self.equity_curve.append(self.risk_manager.capital)

    def _calc_pnl(self, direction, entry, exit, size):
        if direction == "long":
            return (exit - entry) * size
        return (entry - exit) * size

    def _calc_tp(self, entry, sl, direction, rr):
        risk = abs(entry - sl)
        if direction == "long":
            return entry + risk * rr
        return entry - risk * rr

    def _write_csv_header(self):
        """Write CSV header if file doesn't exist."""
        path = Path(self.trade_log_path)
        if not path.exists():
            header = "symbol,signal_time,entry_time,exit_time,direction,entry_price,exit_price,stop_loss,position_size,pnl,exit_reason,phase,range_id,partial_exited\n"
            path.write_text(header)

    def _append_csv(self, trade: Dict):
        """Append a trade record to the CSV log."""
        st = trade.get("signal_time", "")
        line = (
            f"{trade['symbol']},{st},{trade['entry_time']},{trade['exit_time']},"
            f"{trade['direction']},{trade['entry_price']:.2f},{trade['exit_price']:.2f},"
            f"{trade['stop_loss']:.2f},{trade['position_size']:.6f},{trade['pnl']:.2f},"
            f"{trade['exit_reason']},{trade['phase']},{trade['range_id']},{trade['partial_exited']}\n"
        )
        with open(self.trade_log_path, "a") as f:
            f.write(line)

    def _notify(self, message: str):
        """Send notification: Telegram + console already done by logger."""
        if self.telegram_token and self.telegram_chat_id:
            self._send_telegram(message)

    def _send_telegram(self, message: str):
        """Send Telegram notification via HTTP API."""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": self.telegram_chat_id,
                "text": f"[CRT {self.symbol}] {message}",
                "parse_mode": "HTML",
            }).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            log.warning(f"Telegram send failed: {e}")

    def _compute_cost(self, size: float, price: float) -> float:
        """Compute total cost: fixed + percentage of notional."""
        return self.transaction_cost + size * price * self.fee_rate

    def _make_serializable(self, obj):
        """Recursively convert non-serializable types to strings."""
        if isinstance(obj, (pd.Timestamp, datetime)):
            return str(obj)
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._make_serializable(v) for v in obj]
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        return obj

    def _save_state(self):
        """Save current state to JSON (supports restart recovery)."""
        state = {
            "positions": self._make_serializable([
                {k: v for k, v in p.items()}
                for p in self.positions
            ]),
            "pending_orders_count": len(self.pending_orders),
            "pending_ltf_count": len(self.pending_ltf_orders),
            "pending_signals_count": len(self.pending_signals),
            "trades_count": len(self.trades),
            "equity": self.risk_manager.capital,
            "last_4h_ts": str(self.last_4h_ts) if self.last_4h_ts else None,
            "last_15m_ts": str(self.last_15m_ts) if self.last_15m_ts else None,
        }
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=2)

    def _poll_loop(self):
        """Main loop: poll every 60s, detect new candles, process."""
        poll_interval = 60
        log.info(f"PaperTrader started: {self.symbol} mode={self.entry_mode} ltf={self.use_ltf}")
        self._notify(f"PaperTrader STARTED {self.symbol} | mode={self.entry_mode} | capital=${self.initial_capital:,.0f}")

        while self.running:
            try:
                df_4h_new = self._fetch_ohlcv("4h", limit=150)
                df_15m_new = self._fetch_ohlcv("15m", limit=200) if self.use_ltf else pd.DataFrame()

                has_new_4h = self._is_new_4h_candle(df_4h_new) if not df_4h_new.empty else False
                has_new_15m = self._is_new_15m_candle(df_15m_new) if not df_15m_new.empty else False

                if has_new_4h and not df_4h_new.empty:
                    self.df_4h = df_4h_new
                    self.last_4h_ts = self.df_4h.index[-1]
                    log.info(f"New 4h candle: {self.last_4h_ts}")
                    self._update_trailing_stops()
                    self._check_positions()
                    self._check_retests()
                    self._check_limit_orders()
                    self._process_4h_candle()

                if has_new_15m and not df_15m_new.empty:
                    self.df_15m = df_15m_new
                    self.last_15m_ts = self.df_15m.index[-1]
                    self._check_ltf_fills()

                self._save_state()

            except Exception as e:
                log.error(f"Poll cycle error: {e}", exc_info=True)
                time.sleep(5)

            time.sleep(poll_interval)

    def start(self):
        """Start the paper trading loop."""
        self.running = True
        try:
            self._poll_loop()
        except KeyboardInterrupt:
            log.info("Shutdown requested")
        finally:
            self.running = False
            self._save_state()
            summary = f"PaperTrader STOPPED | Trades: {len(self.trades)} | Equity: ${self.risk_manager.capital:,.2f}"
            log.info(summary)
            self._notify(summary)


def main():
    """Run the paper trader from command line."""
    import argparse
    parser = argparse.ArgumentParser(description="CRT Paper Trader")
    parser.add_argument("--exchange", default="binance", help="CCXT exchange ID")
    parser.add_argument("--symbol", default="BTC/USDT", help="Trading pair")
    parser.add_argument("--mode", default="limit_retest", choices=["immediate", "limit_retest", "ltf"],
                        help="Entry mode")
    parser.add_argument("--ltf", action="store_true", help="Enable LTF execution (ltf mode only)")
    parser.add_argument("--capital", type=float, default=10_000, help="Initial capital")
    parser.add_argument("--risk", type=float, default=0.02, help="Risk per trade")
    parser.add_argument("--leverage", type=float, default=3.0, help="Max leverage")
    parser.add_argument("--stop-loss-pct", type=float, default=0.02, help="Stop loss %")
    parser.add_argument("--tp1", type=float, default=1.5, help="TP1 R:R ratio")
    parser.add_argument("--tp2", type=float, default=2.0, help="TP2 R:R ratio")
    parser.add_argument("--entry-logic", default="extreme", choices=["extreme", "conservative"],
                        help="Entry logic for limit_retest mode")
    parser.add_argument("--fee-rate", type=float, default=0.0, help="Percentage fee (e.g. 0.0004 = 0.04%%)")
    parser.add_argument("--telegram-token", help="Telegram bot token")
    parser.add_argument("--telegram-chat", help="Telegram chat ID")
    args = parser.parse_args()

    trader = PaperTrader(
        exchange_id=args.exchange,
        symbol=args.symbol,
        entry_mode=args.mode,
        use_ltf=args.ltf,
        initial_capital=args.capital,
        risk_per_trade=args.risk,
        max_leverage=args.leverage,
        stop_loss_pct=args.stop_loss_pct,
        tp_ratios=[args.tp1, args.tp2],
        entry_logic=args.entry_logic,
        fee_rate=args.fee_rate,
        telegram_token=args.telegram_token,
        telegram_chat_id=args.telegram_chat,
    )
    trader.start()


if __name__ == "__main__":
    main()
