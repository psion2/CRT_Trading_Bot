"""Try stooq and other sources for forex data."""
import pandas as pd

# Try stooq
try:
    df = pd.read_csv('https://stooq.com/q/d/l/?s=eurusd&i=15', parse_dates=True)
    print(f'Stooq EURUSD 15m: {len(df)} rows')
    print(df.head())
except Exception as e:
    print(f'Stooq failed: {e}')

# Try investing.com or other
try:
    from pandas_datareader import data as pdr
    import yfinance as yf
    yf.pdr_override()
    df = pdr.get_data_yahoo('EURUSD=X', interval='15m', period='60d')
    print(f'PDR EURUSD 15m: {len(df)} rows')
except Exception as e:
    print(f'PDR failed: {e}')
