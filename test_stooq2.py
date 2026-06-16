"""Try stooq with better parsing."""
import pandas as pd

# stooq format 
df = pd.read_csv('https://stooq.com/q/d/l/?s=eurusd&i=15', skiprows=1, names=['date','open','high','low','close','volume'], parse_dates=['date'], index_col='date')
if len(df) > 0:
    print(f'Stooq EURUSD 15m: {len(df)} rows, {df.index[0]} to {df.index[-1]}')
    print(df.head(3))
else:
    print('No stooq data')

# Try XAU
df2 = pd.read_csv('https://stooq.com/q/d/l/?s=xauusd&i=15', skiprows=1, names=['date','open','high','low','close','volume'], parse_dates=['date'], index_col='date')
if len(df2) > 0:
    print(f'Stooq XAUUSD 15m: {len(df2)} rows, {df2.index[0]} to {df2.index[-1]}')
else:
    print('No stooq data for XAU')
