"""Test Alpha Vantage API."""
import requests

KEY = 'SM1AU2SHJ8PHXKT3'

# Test EUR/USD 15m with outputsize=full
url = f'https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol=EUR&to_symbol=USD&interval=15min&outputsize=full&apikey={KEY}'
resp = requests.get(url, timeout=30)
data = resp.json()

if 'Time Series FX (15min)' in data:
    ts = data['Time Series FX (15min)']
    dates = sorted(ts.keys())
    print(f'EUR/USD 15m: {len(ts)} candles')
    print(f'Range: {dates[0]} to {dates[-1]}')
    print(f'Sample: {ts[dates[0]]}')
else:
    print(f'Error: {list(data.keys())[:3]}')
    if 'Note' in data:
        print(f'  Note: {data["Note"]}')
    if 'Error Message' in data:
        print(f'  Error: {data["Error Message"]}')

# Test if XAU/USD works
url2 = f'https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol=XAU&to_symbol=USD&interval=15min&outputsize=full&apikey={KEY}'
resp2 = requests.get(url2, timeout=30)
data2 = resp2.json()
if 'Time Series FX (15min)' in data2:
    ts2 = data2['Time Series FX (15min)']
    print(f'\nXAU/USD 15m: {len(ts2)} candles')
else:
    print(f'\nXAU/USD: {list(data2.keys())[:3]}')
