"""Check GitHub forex historical data availability."""
import requests

urls = [
    'https://raw.githubusercontent.com/nichel/forex-historical-data/main/EURUSD_M15_2024.csv',
    'https://raw.githubusercontent.com/nichel/forex-historical-data/main/GBPUSD_M15_2024.csv',
    'https://raw.githubusercontent.com/nichel/forex-historical-data/main/XAUUSD_M15_2024.csv',
    'https://raw.githubusercontent.com/nichel/forex-historical-data/main/EURUSD_M15_2023.csv',
    'https://raw.githubusercontent.com/nichel/forex-historical-data/main/EURUSD_M15_2025.csv',
]

for url in urls:
    resp = requests.head(url, timeout=10)
    fname = url.split('/')[-1]
    cl = resp.headers.get('Content-Length', '?')
    print(f'{fname} -> {resp.status_code} len={cl}')
