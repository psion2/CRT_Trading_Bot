"""
Utility functions for CRT Trading Bot.
"""

import pandas as pd
import numpy as np


def calculate_candle_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate candle range metrics for CRT analysis.

    Adds columns:
    - body: Absolute body size
    - body_pct: Body as percentage of full range
    - upper_wick: Upper wick size
    - lower_wick: Lower wick size
    - wick_to_body: Ratio of wick to body
    - range_pct: Full range as percentage of close
    - candle_type: "bullish", "bearish", or "neutral"
    """
    df = df.copy()

    # Full range
    df["range"] = df["high"] - df["low"]

    # Body
    df["body"] = abs(df["close"] - df["open"])

    # Body direction
    df["body_direction"] = np.where(df["close"] > df["open"], 1, -1)

    # Upper and lower wicks
    df["upper_wick"] = np.where(
        df["body_direction"] == 1,
        df["high"] - df["close"],
        df["high"] - df["open"],
    )
    df["lower_wick"] = np.where(
        df["body_direction"] == 1,
        df["open"] - df["low"],
        df["close"] - df["low"],
    )

    # Percentages
    df["body_pct"] = df["body"] / df["range"]
    df["upper_wick_pct"] = df["upper_wick"] / df["range"]
    df["lower_wick_pct"] = df["lower_wick"] / df["range"]
    df["range_pct"] = (df["range"] / df["close"]) * 100

    # Wick to body ratio
    df["wick_to_body"] = np.where(
        df["body"] > 0,
        df[["upper_wick", "lower_wick"]].max(axis=1) / df["body"],
        0,
    )

    # Candle type
    df["candle_type"] = np.where(
        df["close"] > df["open"],
        "bullish",
        np.where(df["close"] < df["open"], "bearish", "neutral"),
    )

    return df


def calculate_atr(
    df: pd.DataFrame,
    period: int = 14,
) -> pd.Series:
    """
    Calculate Average True Range (ATR).

    Args:
        df: DataFrame with high, low, close columns
        period: ATR period

    Returns:
        Series with ATR values
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()

    return atr


def detect_support_resistance(
    df: pd.DataFrame,
    window: int = 20,
) -> dict:
    """
    Detect support and resistance levels.

    Returns:
        Dict with 'support' and 'resistance' levels
    """
    recent_high = df["high"].rolling(window=window).max()
    recent_low = df["low"].rolling(window=window).min()

    return {
        "resistance": recent_high.iloc[-1],
        "support": recent_low.iloc[-1],
    }