"""
Risk management module for CRT Trading Bot.
Handles position sizing, stop loss, and take profit calculations.
"""

import pandas as pd
from typing import Tuple, Optional


class RiskManager:
    def __init__(
        self,
        capital: float = 10_000,
        risk_per_trade: float = 0.03,
    ):
        """
        Initialize RiskManager.

        Args:
            capital: Starting capital in USD
            risk_per_trade: Risk percentage per trade (0.03 = 3%)
        """
        self.capital = capital
        self.initial_capital = capital
        self.risk_per_trade = risk_per_trade

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        risk_amount: float = None,
    ) -> float:
        """
        Calculate position size based on risk parameters.

        Args:
            entry_price: Entry price of the trade
            stop_loss: Stop loss price
            risk_amount: Risk amount in USD (defaults to capital * risk_per_trade)

        Returns:
            Position size (number of units)
        """
        if risk_amount is None:
            risk_amount = self.capital * self.risk_per_trade

        risk_per_unit = abs(entry_price - stop_loss)
        position_size = risk_amount / risk_per_unit

        return position_size

    def calculate_stop_loss(
        self,
        entry_price: float,
        direction: str,
        atr: float = None,
        stop_pct: float = 1.5,
    ) -> float:
        """
        Calculate stop loss price.

        Args:
            entry_price: Entry price
            direction: "long" or "short"
            atr: Average True Range (optional)
            stop_pct: Stop loss as percentage of entry (e.g., 0.015 = 1.5%)

        Returns:
            Stop loss price
        """
        if atr:
            # Use ATR-based stop
            if direction == "long":
                return entry_price - (atr * 1.5)
            else:
                return entry_price + (atr * 1.5)
        else:
            # Use percentage-based stop
            if direction == "long":
                return entry_price * (1 - stop_pct)
            else:
                return entry_price * (1 + stop_pct)

    def calculate_take_profit(
        self,
        entry_price: float,
        stop_loss: float,
        direction: str,
        risk_reward_ratio: float = 2.0,
    ) -> float:
        """
        Calculate take profit based on risk-reward ratio.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            direction: "long" or "short"
            risk_reward_ratio: Target R:R ratio

        Returns:
            Take profit price
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward_ratio

        if direction == "long":
            return entry_price + reward
        else:
            return entry_price - reward

    def update_capital(self, pnl: float):
        """Update capital after a trade."""
        self.capital += pnl

    def reset(self):
        """Reset capital to initial value."""
        self.capital = self.initial_capital


if __name__ == "__main__":
    rm = RiskManager(capital=10_000, risk_per_trade=0.03)

    # Example: Long trade
    entry = 50_000
    sl = 49_000
    tp = 52_000

    size = rm.calculate_position_size(entry, sl)
    print(f"Position size: {size}")
    print(f"Risk amount: {abs(entry - sl) * size}")