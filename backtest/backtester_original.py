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
    ):
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.stop_mode = stop_mode
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

    def run(
        self,
        df: pd.DataFrame,
        symbol: str,
        stop_loss_pct: float = 0.02,
        take_profit_ratios: List[float] = [1.5, 2.0],
        ltf_df: pd.DataFrame = None,
    ) -> Dict:
        df = self.strategy.generate_signals(df, ltf_df=ltf_df)
        self.positions = []

        for i in range(len(df)):
            row = df.iloc[i]
            signal = row["signal"]
            current_price = row["close"]

            if signal == 0:
                self._update_trailing_stops(df, i, current_price)
                self._check_exits(df, i, current_price, take_profit_ratios)
                continue

            direction = "long" if signal == 1 else "short"
            range_id = int(row.get("crt_range_id", 0))
            inv_price = row.get("crt_inv_price")
            phase_type = row.get("crt_phase_type", "unknown")

            sl = self._compute_sl(current_price, direction, inv_price, stop_loss_pct)
            risk = abs(current_price - sl)

            if risk <= 0:
                continue

            try:
                position_size = self.risk_manager.calculate_position_size(current_price, sl)
            except:
                position_size = (self.risk_manager.capital * self.risk_per_trade) / risk

            trade = {
                "symbol": symbol, "entry_time": df.index[i], "entry_price": current_price,
                "direction": direction, "position_size": position_size, "stop_loss": sl,
                "original_sl": sl, "original_risk": risk, "partial_exited": False,
                "status": "open", "range_id": range_id, "phase": phase_type,
            }
            self.positions.append(trade)

            self._update_trailing_stops(df, i, current_price)
            self._check_exits(df, i, current_price, take_profit_ratios)

        for pos in list(self.positions):
            if pos["status"] == "open":
                final_price = df.iloc[-1]["close"]
                pnl = self._calculate_pnl(pos["direction"], pos["entry_price"], final_price, pos["position_size"])
                self._close_trade(pos, df.index[-1], final_price, pnl, "EOD")

        return self._calculate_metrics()

    def _compute_sl(self, price: float, direction: str, inv_price, fallback_pct: float) -> float:
        if inv_price is not None and not (isinstance(inv_price, float) and np.isnan(inv_price)):
            return float(inv_price)
        if direction == "long":
            sl = price * (1 - fallback_pct)
            return sl if sl != price else price * 0.99
        else:
            sl = price * (1 + fallback_pct)
            return sl if sl != price else price * 1.01

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
        inv_price = row.get("crt_inv_price")
        if inv_price is None or (isinstance(inv_price, float) and np.isnan(inv_price)):
            return

        for pos in self.positions:
            if pos["status"] != "open":
                continue
            if pos.get("range_id", 0) == new_range_id and pos.get("entry_time") < df.index[idx]:
                if pos["direction"] == "long":
                    if float(inv_price) > pos["stop_loss"]:
                        pos["stop_loss"] = float(inv_price)
                else:
                    if float(inv_price) < pos["stop_loss"]:
                        pos["stop_loss"] = float(inv_price)

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
                    partial = pos.copy()
                    partial.update({"exit_time": df.index[idx], "exit_price": tp1, "pnl": pnl_partial,
                                    "exit_reason": "TP1_50%", "position_size": half_size, "status": "closed"})
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
        """Close a trade and record results."""
        trade["exit_time"] = exit_time
        trade["exit_price"] = exit_price
        trade["pnl"] = pnl
        trade["exit_reason"] = exit_reason
        trade["status"] = "closed"

        self.trades.append(trade)
        self.risk_manager.update_capital(pnl)
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