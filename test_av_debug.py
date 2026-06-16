"""Debug Alpha Vantage response."""
import requests

KEY = 'SM1AU2SHJ8PHXKT3'
url = f'https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol=EUR&to_symbol=USD&interval=15min&outputsize=full&apikey={KEY}'
resp = requests.get(url, timeout=30)
print(resp.text[:500])
