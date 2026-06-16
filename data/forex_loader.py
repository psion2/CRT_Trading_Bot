"""
Forex Data Loader for CRT Trading Bot
Loads forex data from local CSV files
"""

import pandas as pd
import os
from pathlib import Path


class ForexDataLoader:
    """Load forex data from CSV files."""

    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "forex"
        self.data_dir = Path(data_dir)

    def load_forex(self, pair: str, timeframe: str = "4h") -> pd.DataFrame:
        """
        Load forex pair data.

        Args:
            pair: Pair name (e.g., 'EUR_USD', 'GBP_USD')
            timeframe: Timeframe (e.g., '4h', '1h', '15m')

        Returns:
            DataFrame with OHLCV data
        """
        filename = f"{pair}_{timeframe}.csv"
        filepath = self.data_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        df = pd.read_csv(filepath, index_col=0, parse_dates=True)

        # Standardize column names
        df.columns = [col.lower() for col in df.columns]

        # Ensure required columns exist
        required = ['open', 'high', 'low', 'close']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing column: {col}")

        # Add volume if not present
        if 'volume' not in df.columns:
            df['volume'] = 0

        return df

    def list_available_pairs(self):
        """List all available forex pairs."""
        files = self.data_dir.glob("*.csv")
        pairs = set()
        for f in files:
            # Extract pair name from filename (e.g., EUR_USD from EUR_USD_4h.csv)
            name = f.stem.rsplit("_", 1)[0]
            pairs.add(name)
        return sorted(pairs)

    def get_all_forex_data(self, timeframe: str = "4h") -> dict:
        """Load all available forex pairs."""
        pairs = self.list_available_pairs()
        data = {}
        for pair in pairs:
            try:
                data[pair] = self.load_forex(pair, timeframe)
            except Exception as e:
                print(f"Error loading {pair}: {e}")
        return data


if __name__ == "__main__":
    loader = ForexDataLoader()

    print("Available forex pairs:")
    print(loader.list_available_pairs())

    print("\nLoading EUR_USD...")
    df = loader.load_forex("EUR_USD")
    print(df.tail())