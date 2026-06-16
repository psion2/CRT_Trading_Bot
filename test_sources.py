"""Try multiple free forex 15m data sources."""
import requests, re, time

sources = [
    # Histdata - different URL patterns
    'https://www.histdata.com/get.php?/metatrader/15-minute-bar-quotes/EURUSD/2025',
    'https://www.histdata.com/download.php?/metatrader/15-minute-bar-quotes/EURUSD/2025',
    # FX historical data
    'https://www.fxhistoricaldata.com/download/EURUSD?timeframe=M15&year=2024',
    'https://www.fxhistoricaldata.com/download/EURUSD_M15_2024.zip',
    # Alternative histdata format
    'https://www.histdata.com/download-free-forex-data/?/metatrader/15-minute-bar-quotes/EURUSD/2025/5',
]

for url in sources:
    try:
        resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html,*/*'})
        print(f'{resp.status_code} {len(resp.content):>7}B -> {url[:70]}')
    except Exception as e:
        print(f'ERR {str(e)[:40]:>40} -> {url[:70]}')
