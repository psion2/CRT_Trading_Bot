"""
Colab Paper Trader for CRT Trading Bot.
Persists state to Google Drive, catches up on restart, serves dashboard via ngrok.
"""
import os, sys, json, time, logging, threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from strategies.crt_strategy import CRTStrategyImpl
from risk.risk_manager import RiskManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


class ColabTrader:
    """Colab-compatible paper trader with Drive persistence and catch-up."""

    def __init__(
        self,
        drive_path: str = "/content/drive/MyDrive/crt_trading",
        exchange_id: str = "bybit",
        symbol: str = "BTC/USDT",
        entry_mode: str = "limit_retest",
        use_ltf: bool = False,
        initial_capital: float = 10_000,
        risk_per_trade: float = 0.02,
        max_leverage: float = 3.0,
        transaction_cost: float = 10.0,
        fee_rate: float = 0.0004,
        retest_window: int = 4,
        ltf_window_hours: int = 18,
        stop_loss_pct: float = 0.02,
        tp_ratios: Optional[list] = None,
        entry_logic: str = "extreme",
    ):
        self.drive_path = Path(drive_path)
        self.drive_path.mkdir(parents=True, exist_ok=True)
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

        self.state_path = self.drive_path / "trader_state.json"
        self.trade_log_path = self.drive_path / "trade_log.csv"
        self.equity_path = self.drive_path / "equity_curve.json"
        self.log_path = self.drive_path / "colab_trader.log"

        self._setup_logging()

        self.strategy = CRTStrategyImpl(
            use_kod=True, use_model1=True, use_ote=True,
            use_breaker_block=True, use_candle3_only=True, use_true_mss=True,
        )
        self.risk_manager = RiskManager(capital=initial_capital, risk_per_trade=risk_per_trade)

        self.exchange = None
        self.df_4h = pd.DataFrame()
        self.df_15m = pd.DataFrame()
        self.last_4h_ts: Optional[pd.Timestamp] = None
        self.last_15m_ts: Optional[pd.Timestamp] = None
        self.processed_signal_indices: set = set()
        self.positions: list = []
        self.pending_signals: list = []
        self.pending_orders: list = []
        self.pending_ltf_orders: list = []
        self.trades: list = []
        self.missed_orders: list = []
        self.equity_curve: list = [initial_capital]
        self.running = False
        self.poll_interval = 60
        self.catch_up_mode = False

        self._init_exchange()
        self._load_state()
        self._write_csv_header()

    def _setup_logging(self):
        fh = logging.FileHandler(self.log_path)
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        log.addHandler(fh)

    def _init_exchange(self):
        import ccxt
        fallbacks = [self.exchange_id, 'kucoin', 'bybit', 'binance', 'mexc', 'gate']
        fallbacks = list(dict.fromkeys(fallbacks))  # deduplicate preserving order
        for exch_id in fallbacks:
            try:
                self.exchange = getattr(ccxt, exch_id)({"enableRateLimit": True})
                self.exchange.load_markets()
                self.exchange_id = exch_id
                log.info(f"Connected to {exch_id}")
                return
            except Exception as e:
                log.warning(f"Exchange {exch_id} failed: {e}")
        raise RuntimeError(f"No exchange available from: {fallbacks}")

    def _fetch_ohlcv(self, timeframe: str, limit: int = 200) -> pd.DataFrame:
        try:
            raw = self.exchange.fetch_ohlcv(self.symbol, timeframe, limit=limit)
            df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            return df
        except Exception as e:
            log.warning(f"fetch_ohlcv ({timeframe}) failed: {e}")
            return pd.DataFrame()

    def _make_serializable(self, obj):
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
        state = {
            "positions": self._make_serializable(self.positions),
            "pending_orders": self._make_serializable(self.pending_orders),
            "pending_signals": self._make_serializable(self.pending_signals),
            "pending_ltf_orders": self._make_serializable(self.pending_ltf_orders),
            "trades_count": len(self.trades),
            "equity": self.risk_manager.capital,
            "last_4h_ts": str(self.last_4h_ts) if self.last_4h_ts else None,
            "processed_indices": [str(i) for i in self.processed_signal_indices],
            "updated_at": str(datetime.now()),
        }
        try:
            with open(self.state_path, "w") as f:
                json.dump(state, f, indent=2)
            with open(self.equity_path, "w") as f:
                json.dump(self.equity_curve, f)
        except Exception as e:
            log.error(f"Save state failed: {e}")

    def _load_state(self):
        if not self.state_path.exists():
            log.info("No saved state found - starting fresh")
            return
        try:
            with open(self.state_path) as f:
                state = json.load(f)
            self.positions = state.get("positions", [])
            self.risk_manager.capital = state.get("equity", self.initial_capital)
            self.equity_curve = json.loads(self.equity_path.read_text()) if self.equity_path.exists() else [self.risk_manager.capital]
            self.pending_orders = state.get("pending_orders", [])
            self.pending_signals = state.get("pending_signals", [])
            self.pending_ltf_orders = state.get("pending_ltf_orders", [])
            self.processed_signal_indices = set(state.get("processed_indices", []))
            last_ts = state.get("last_4h_ts")
            if last_ts:
                self.last_4h_ts = pd.Timestamp(last_ts)
            log.info(f"State loaded: {len(self.positions)} positions, ${self.risk_manager.capital:.0f} capital")
        except Exception as e:
            log.error(f"Load state failed: {e}")

    def _catch_up(self):
        """Process all 4H candles missed since last known timestamp."""
        df = self._fetch_ohlcv("4h", limit=150)
        if df.empty:
            return
        if self.last_4h_ts is None:
            self.df_4h = df
            self.last_4h_ts = df.index[-1]
            return
        new_candles = df[df.index > self.last_4h_ts]
        if new_candles.empty:
            self.df_4h = df
            return
        log.info(f"Catching up: {len(new_candles)} missed 4H candles since {self.last_4h_ts}")
        self.catch_up_mode = True
        self.df_4h = df
        for ts in new_candles.index:
            self.df_4h = df[df.index <= ts]
            self.last_4h_ts = ts
            self._process_4h_candle()
            self._update_trailing_stops()
            self._check_positions()
            self._check_retests()
            self._check_limit_orders()
            if self.use_ltf:
                ltf = self._fetch_ohlcv("15m", limit=200)
                if not ltf.empty:
                    self.df_15m = ltf
                    self._check_ltf_fills()
            self._save_state()
            log.info(f"  Catch-up: processed {ts}")
        self.catch_up_mode = False
        log.info(f"Catch-up complete. State saved.")

    def _process_4h_candle(self):
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
        range_id = int(row.get("crt_range_id", 0))
        inv_price = row.get("crt_inv_price")
        stop_price = row.get("crt_stop_price")
        phase_type = row.get("crt_phase_type", "unknown")
        current_price = row["close"]
        crt_entry = float(inv_price) if inv_price is not None and isinstance(inv_price, (int, float)) and not np.isnan(inv_price) else None
        msg = f"SIGNAL {direction.upper()} {phase_type} range={range_id} inv=${crt_entry:,.0f} price=${current_price:,.0f}"
        log.info(msg)

        if self.entry_mode == "immediate":
            if phase_type == "Model-1" and self.retest_window > 0 and crt_entry is not None:
                self.pending_signals.append({
                    "entry_level": crt_entry, "direction": direction, "signal_idx": idx,
                    "signal_time": idx, "phase": phase_type, "range_id": range_id,
                    "stop_price": stop_price, "inv_price": inv_price, "symbol": self.symbol,
                })
                return
            self._open_trade(crt_entry or current_price, direction, range_id, phase_type, stop_price, inv_price, signal_time=idx)

        elif self.entry_mode == "limit_retest":
            extreme = crt_entry if crt_entry is not None else current_price
            close_price = current_price
            if phase_type == "Model-1":
                fill_levels = [close_price, extreme] if self.entry_logic == "conservative" else [extreme]
                self.pending_orders.append({
                    "entry_level": extreme, "fill_levels": fill_levels, "direction": direction,
                    "signal_idx": idx, "signal_time": idx, "phase": phase_type, "range_id": range_id,
                    "stop_price": stop_price, "inv_price": inv_price, "symbol": self.symbol,
                    "stop_loss_pct": self.stop_loss_pct,
                })
            else:
                fill_levels = [close_price, extreme] if self.entry_logic == "conservative" else [extreme]
                for level in fill_levels:
                    if (direction == "long" and row["low"] <= level) or (direction == "short" and row["high"] >= level):
                        self._open_trade(level, direction, range_id, phase_type, stop_price, inv_price, signal_time=idx)
                        self.pending_orders = [o for o in self.pending_orders if o.get("range_id") != range_id]
                        break

        elif self.entry_mode == "ltf" and self.use_ltf:
            close_time = idx + pd.Timedelta(hours=4)
            self.pending_ltf_orders.append({
                "direction": direction, "inv_price": inv_price, "stop_price": stop_price,
                "range_id": range_id, "phase": phase_type, "symbol": self.symbol,
                "signal_close_time": close_time, "signal_idx": idx, "signal_time": idx,
                "stop_loss_pct": self.stop_loss_pct,
            })

    def _check_retests(self):
        for pending in list(self.pending_signals):
            if self.df_4h.empty: continue
            last = self.df_4h.iloc[-1]
            level = pending["entry_level"]
            retested = (pending["direction"] == "long" and last["low"] <= level) or \
                       (pending["direction"] == "short" and last["high"] >= level)
            if retested:
                self._open_trade(level, pending["direction"], pending["range_id"], pending["phase"],
                                 pending["stop_price"], pending["inv_price"], signal_time=pending.get("signal_time"))
                self.pending_signals.remove(pending)
                log.info(f"  M1 retested at ${level:,.0f}: FILLED")
            elif len(self.df_4h) - self.df_4h.index.get_loc(pending["signal_time"]) > self.retest_window:
                self.missed_orders.append(pending)
                self.pending_signals.remove(pending)

    def _check_limit_orders(self):
        if self.df_4h.empty or self.entry_mode != "limit_retest": return
        last = self.df_4h.iloc[-1]
        for order in list(self.pending_orders):
            level = None; filled = False
            for test_level in order["fill_levels"]:
                if order["direction"] == "long" and last["low"] <= test_level:
                    level = test_level; filled = True; break
                elif order["direction"] == "short" and last["high"] >= test_level:
                    level = test_level; filled = True; break
            if filled:
                if any(p.get("range_id") == order["range_id"] and p["status"] == "open" for p in self.positions):
                    self.pending_orders.remove(order); continue
                self._open_trade(level, order["direction"], order["range_id"], order["phase"],
                                 order["stop_price"], order["inv_price"], signal_time=order.get("signal_time"))
                self.pending_orders.remove(order)
            elif len(self.df_4h) > 1:
                ci = self.df_4h.index.get_loc(self.df_4h.index[-1])
                si = self.df_4h.index.get_loc(order["signal_idx"]) if order["signal_idx"] in self.df_4h.index else ci
                if ci - si > self.retest_window:
                    self.missed_orders.append(order)
                    self.pending_orders.remove(order)

    def _check_ltf_fills(self):
        if self.df_15m.empty or not self.use_ltf or self.df_4h.empty: return
        candle_time = self.df_4h.index[-1]; candle_end = candle_time + timedelta(hours=4)
        for order in list(self.pending_ltf_orders):
            close_time = order["signal_close_time"]; window_end = close_time + timedelta(hours=self.ltf_window_hours)
            if candle_time >= window_end:
                self.missed_orders.append(order); self.pending_ltf_orders.remove(order); continue
            inv_price = float(order["inv_price"]); filled = False; entry_price = None
            if candle_time == close_time:
                concurrent_ts = close_time - timedelta(minutes=15)
                if concurrent_ts in self.df_15m.index:
                    c = self.df_15m.loc[concurrent_ts]
                    if order["direction"] == "long" and c["close"] > inv_price: filled = True; entry_price = c["close"]
                    elif order["direction"] == "short" and c["close"] < inv_price: filled = True; entry_price = c["close"]
            if not filled:
                scan_start = max(close_time, candle_time)
                ltfs = self.df_15m[self.df_15m.index >= scan_start]
                ltfs = ltfs[ltfs.index <= candle_end] if not ltfs.empty else ltfs
                if not ltfs.empty:
                    if ltfs.index[0] == scan_start == close_time: ltfs = ltfs.iloc[1:]
                    if not ltfs.empty:
                        if order["phase"] == "KOD":
                            m1 = self._detect_ltf_model1(ltfs, order["direction"], inv_price)
                            if m1: filled = True; entry_price = m1[1]
                        else:
                            for j in range(len(ltfs)):
                                c = ltfs.iloc[j]["close"]
                                if order["direction"] == "long" and c > inv_price: filled = True; entry_price = c; break
                                elif order["direction"] == "short" and c < inv_price: filled = True; entry_price = c; break
            if filled and entry_price is not None:
                self._open_trade(entry_price, order["direction"], order["range_id"], order["phase"],
                                 order["stop_price"], order["inv_price"], signal_time=order.get("signal_time"))
                self.pending_ltf_orders.remove(order)

    def _detect_ltf_model1(self, data, direction, inv_price):
        inv_price = float(inv_price)
        for i in range(len(data) - 1):
            c = data.iloc[i]; body = abs(c["close"] - c["open"]); rng = c["high"] - c["low"]
            if rng <= 0 or body / rng < 0.7: continue
            nc = data.iloc[i + 1]
            if direction == "long":
                if c["close"] < c["open"] and c["low"] <= inv_price * 1.005 and nc["close"] > c["high"]:
                    entry = c["low"]
                    for j in range(i + 2, len(data)):
                        if data.iloc[j]["low"] <= entry: return data.index[j], entry
            else:
                if c["close"] > c["open"] and c["high"] >= inv_price * 0.995 and nc["close"] < c["low"]:
                    entry = c["high"]
                    for j in range(i + 2, len(data)):
                        if data.iloc[j]["high"] >= entry: return data.index[j], entry
        return None

    def _update_trailing_stops(self):
        if self.df_4h.empty: return
        row = self.df_4h.iloc[-1]; signal = row.get("signal", 0)
        if signal == 0: return
        rid = int(row.get("crt_range_id", 0))
        if rid == 0: return
        sp = row.get("crt_stop_price")
        if sp is None or (isinstance(sp, float) and np.isnan(sp)): return
        sd = int(signal)
        if sd == 0: return
        for pos in self.positions:
            if pos["status"] != "open": continue
            if pos.get("range_id", 0) == rid:
                if (pos["direction"] == "long" and sd != 1) or (pos["direction"] == "short" and sd != -1): continue
                ns = float(sp)
                if pos["direction"] == "long" and ns > pos["stop_loss"]: pos["stop_loss"] = ns
                elif pos["direction"] == "short" and ns < pos["stop_loss"]: pos["stop_loss"] = ns

    def _compute_cost(self, size, price):
        return self.transaction_cost + size * price * self.fee_rate

    def _compute_sl(self, entry_price, direction, stop_price):
        if stop_price is not None and isinstance(stop_price, (int, float)) and not np.isnan(stop_price):
            s = float(stop_price)
            if direction == "long" and s < entry_price: return s
            elif direction == "short" and s > entry_price: return s
        return entry_price * (1 - self.stop_loss_pct if direction == "long" else 1 + self.stop_loss_pct)

    def _open_trade(self, entry_price, direction, range_id, phase_type, stop_price, inv_price, signal_time=None):
        sl = self._compute_sl(entry_price, direction, stop_price)
        risk = abs(entry_price - sl)
        if risk <= 0: return
        existing = [p for p in self.positions if p.get("range_id") == range_id and p["status"] == "open"]
        if existing:
            pos = existing[0]
            bs = (self.initial_capital * self.risk_per_trade) / pos.get("original_risk", risk); a = bs * 0.5
            if direction == "long":
                if sl > pos["stop_loss"]: pos["stop_loss"] = sl
            else:
                if sl < pos["stop_loss"]: pos["stop_loss"] = sl
            pos["position_size"] += a; pos["phase"] = f"{pos['phase']}+{phase_type}"
            mn = self.initial_capital * self.max_leverage
            if pos["position_size"] * pos["entry_price"] > mn: pos["position_size"] = mn / pos["entry_price"]
            log.info(f"  SCALE-IN {direction.upper()} {phase_type} range={range_id} size={a:.4f} @ ${entry_price:,.0f}")
            return
        ps = (self.initial_capital * self.risk_per_trade) / risk
        mn = self.initial_capital * self.max_leverage
        if ps * entry_price > mn: ps = mn / entry_price
        self.positions.append({
            "symbol": self.symbol, "signal_time": signal_time, "entry_time": datetime.now(),
            "entry_price": entry_price, "direction": direction, "position_size": ps, "stop_loss": sl,
            "original_sl": sl, "original_risk": risk, "partial_exited": False, "status": "open",
            "range_id": range_id, "phase": phase_type, "inv_price": inv_price, "stop_price": stop_price,
        })
        log.info(f"  ENTRY {direction.upper()} {phase_type} range={range_id} size={ps:.4f} @ ${entry_price:,.0f} SL=${sl:,.0f}")

    def _check_positions(self):
        if self.df_4h.empty: return
        cp = self.df_4h.iloc[-1]["close"]
        for pos in list(self.positions):
            if pos["status"] != "open": continue
            r = pos.get("original_risk", abs(pos["entry_price"] - pos["stop_loss"]))
            d = pos["direction"]
            sl_hit = (d == "long" and cp <= pos["stop_loss"]) or (d == "short" and cp >= pos["stop_loss"])
            if sl_hit:
                p = self._calc_pnl(d, pos["entry_price"], pos["stop_loss"], pos["position_size"])
                self._close_trade(pos, cp, p, "SL"); continue
            tp1 = self._calc_tp(pos["entry_price"], pos["original_sl"], d, self.tp_ratios[0])
            tp_hit = (d == "long" and cp >= tp1) or (d == "short" and cp <= tp1)
            if tp_hit and not pos.get("partial_exited", False):
                h = pos["position_size"] * 0.5; ec = self._compute_cost(h, tp1)
                pp = self._calc_pnl(d, pos["entry_price"], tp1, h) - ec
                self._record_close(pos, datetime.now(), tp1, pp, "TP1_50%", h)
                pos["position_size"] = h; pos["stop_loss"] = pos["entry_price"]; pos["partial_exited"] = True
                if len(self.tp_ratios) > 1:
                    tp2 = self._calc_tp(pos["entry_price"], pos.get("original_sl", pos["stop_loss"]), d, self.tp_ratios[1])
                    tp2_hit = (d == "long" and cp >= tp2) or (d == "short" and cp <= tp2)
                    if tp2_hit:
                        pf = self._calc_pnl(d, pos["entry_price"], tp2, pos["position_size"])
                        self._close_trade(pos, cp, pf, "TP2")

    def _close_trade(self, pos, exit_price, pnl, reason):
        ec = self._compute_cost(pos["position_size"], pos["entry_price"])
        xc = self._compute_cost(pos["position_size"], exit_price)
        npnl = pnl - (ec + xc)
        self._record_close(pos, datetime.now(), exit_price, npnl, reason, pos["position_size"])
        pos["status"] = "closed"
        log.info(f"  CLOSE {reason} {pos['direction'].upper()} {pos['phase']} PnL=${npnl:,.2f}")

    def _record_close(self, pos, exit_time, exit_price, pnl, reason, size):
        self.trades.append({
            "symbol": self.symbol, "signal_time": str(pos.get("signal_time", "")),
            "entry_time": str(pos["entry_time"]), "exit_time": str(exit_time),
            "direction": pos["direction"], "entry_price": pos["entry_price"],
            "exit_price": exit_price, "stop_loss": pos["stop_loss"],
            "position_size": size, "pnl": pnl, "exit_reason": reason,
            "phase": pos["phase"], "range_id": pos["range_id"],
            "partial_exited": pos.get("partial_exited", False),
        })
        self._append_csv(self.trades[-1])
        self.risk_manager.update_capital(pnl)
        self.equity_curve.append(self.risk_manager.capital)

    def _calc_pnl(self, d, e, ex, s):
        return (ex - e) * s if d == "long" else (e - ex) * s

    def _calc_tp(self, e, sl, d, rr):
        r = abs(e - sl)
        return e + r * rr if d == "long" else e - r * rr

    def _write_csv_header(self):
        if not self.trade_log_path.exists():
            self.trade_log_path.write_text("symbol,signal_time,entry_time,exit_time,direction,entry_price,exit_price,stop_loss,position_size,pnl,exit_reason,phase,range_id,partial_exited\n")

    def _append_csv(self, t):
        line = f"{t['symbol']},{t.get('signal_time','')},{t['entry_time']},{t['exit_time']},{t['direction']},{t['entry_price']:.2f},{t['exit_price']:.2f},{t['stop_loss']:.2f},{t['position_size']:.6f},{t['pnl']:.2f},{t['exit_reason']},{t['phase']},{t['range_id']},{t['partial_exited']}\n"
        with open(self.trade_log_path, "a") as f: f.write(line)

    def _keepalive(self):
        """Ping every 30s to prevent Colab inactivity timeout."""
        while self.running:
            time.sleep(30)
            log.debug("Keepalive ping")

    def _start_ngrok_dashboard(self):
        """Serve a mini dashboard via ngrok tunnel."""
        try:
            from flask import Flask, jsonify
            from flask_cors import CORS
            from pyngrok import ngrok
            app_dash = Flask(__name__); CORS(app_dash)

            @app_dash.route("/")
            def index():
                pos_summary = [{
                    "symbol": p["symbol"], "direction": p["direction"],
                    "entry_price": p["entry_price"], "size": p["position_size"],
                    "sl": p["stop_loss"], "phase": p["phase"],
                } for p in self.positions if p["status"] == "open"]
                return jsonify({
                    "capital": self.risk_manager.capital,
                    "total_pnl": self.risk_manager.capital - self.initial_capital,
                    "open_positions": pos_summary,
                    "trades_count": len(self.trades),
                    "last_4h": str(self.last_4h_ts),
                    "uptime": str(datetime.now()),
                })

            @app_dash.route("/trades")
            def trades_route():
                return jsonify(self.trades[-50:])

            public_url = ngrok.connect(5000)
            log.info(f"Dashboard: {public_url}")
        except ImportError:
            log.info("Flask/ngrok not installed - dashboard unavailable")

    def start(self):
        self.running = True
        self._catch_up()
        threading.Thread(target=self._keepalive, daemon=True).start()
        try:
            self._start_ngrok_dashboard()
        except Exception:
            pass
        log.info(f"Live trading started: {self.symbol} mode={self.entry_mode}")
        while self.running:
            try:
                df4 = self._fetch_ohlcv("4h", limit=150)
                df15 = self._fetch_ohlcv("15m", limit=200) if self.use_ltf else pd.DataFrame()
                new4 = self._detect_new_candle(df4, self.df_4h)
                new15 = self._detect_new_candle(df15, self.df_15m) if self.use_ltf else False
                if new4 and not df4.empty:
                    self.df_4h = df4; self.last_4h_ts = df4.index[-1]
                    log.info(f"New 4h: {self.last_4h_ts}")
                    self._update_trailing_stops()
                    self._check_positions()
                    self._check_retests(); self._check_limit_orders()
                    self._process_4h_candle()
                if new15 and not df15.empty:
                    self.df_15m = df15; self.last_15m_ts = df15.index[-1]
                    self._check_ltf_fills()
                self._save_state()
            except Exception as e:
                log.error(f"Cycle error: {e}", exc_info=True)
                time.sleep(5)
            time.sleep(self.poll_interval)

    def _detect_new_candle(self, new_df, old_df):
        if new_df.empty: return None
        if old_df.empty: return new_df.index[-1]
        nt = new_df.index[-1]; ot = old_df.index[-1]
        return nt if nt > ot else None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CRT Colab Trader")
    parser.add_argument("--drive-path", default="/content/drive/MyDrive/crt_trading")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--mode", default="limit_retest", choices=["immediate", "limit_retest", "ltf"])
    parser.add_argument("--ltf", action="store_true")
    parser.add_argument("--capital", type=float, default=10000)
    parser.add_argument("--risk", type=float, default=0.02)
    parser.add_argument("--fee-rate", type=float, default=0.0004)
    args = parser.parse_args()

    trader = ColabTrader(
        drive_path=args.drive_path, symbol=args.symbol, entry_mode=args.mode,
        use_ltf=args.ltf, initial_capital=args.capital, risk_per_trade=args.risk,
        fee_rate=args.fee_rate,
    )
    trader.start()
