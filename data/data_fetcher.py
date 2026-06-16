"""
Data fetching module for CRT Trading Bot.
Uses CCXT for exchange data retrieval.
"""

import ccxt
import pandas as pd
from pathlib import Path


class DataFetcher:
    def __init__(self):
        self.exchanges = {
            "binance": ccxt.binance(),
            "hyperliquid": ccxt.hyperliquid(),
        }

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "4h",
        since: str = None,
        limit: int = 1000,
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from exchange.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            timeframe: Candle timeframe (e.g., "4h", "1d")
            since: Start date in ISO format
            limit: Number of candles to fetch

        Returns:
            DataFrame with OHLCV data
        """
        # Determine exchange based on symbol
        if "USD" in symbol:
            exchange = self.exchanges["binance"]
        elif "GBP" in symbol:
            exchange = self.exchanges["oanda"]
        else:
            exchange = self.exchanges["binance"]

        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)

        df = pd.DataFrame(
            ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        return df

    def fetch_and_save(
        self,
        symbols: list,
        timeframe: str = "4h",
        start_date: str = None,
        limit: int = 1000,
        data_dir: Path = None,
    ) -> dict:
        """
        Fetch and save data for multiple symbols.

        Returns:
            Dict mapping symbol to DataFrame
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"

        data_dir.mkdir(parents=True, exist_ok=True)
        data = {}

        for symbol in symbols:
            print(f"Fetching {symbol}...")
            df = self.fetch_ohlcv(symbol, timeframe, limit=limit)
            filepath = data_dir / f"{symbol.replace('/', '_')}_{timeframe}.csv"
            df.to_csv(filepath)
            print(f"Saved {symbol} to {filepath}")
            data[symbol] = df

        return data


if __name__ == "__main__":
    fetcher = DataFetcher()
    data = fetcher.fetch_ohlcv("BTC/USDT", "4h", limit=500)
    print(data.tail())