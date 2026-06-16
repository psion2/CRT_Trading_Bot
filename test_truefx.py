"""Try TrueFX free historical forex data."""
import requests, time, re

# Known TrueFX data URL pattern
urls = [
    'http://www.truefx.com/dev/data/EURUSD-2024-05.zip',
    'http://www.truefx.com/dev/data/2024/EURUSD-2024-05.zip',
    'http://www.truefx.com/dev/data/EURUSD/EURUSD-2024-05.zip',
    'http://www.truefx.com/dev/data/EURUSD/2024/EURUSD-2024-05.zip',
]

for url in urls:
    try:
        resp = requests.head(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        print(f'{url} -> {resp.status_code}')
        if resp.status_code == 200:
            print(f'  Content-Length: {resp.headers.get("Content-Length", "unknown")}')
    except Exception as e:
        print(f'{url} -> Error: {e}')

# Also try web scraping the page to find links
resp = requests.get('http://www.truefx.com/dev/data/', timeout=10)
if resp.status_code == 200:
    links = re.findall(r'href=[\"\'](.*?)[\"\']', resp.text)
    print(f'\nTrueFX page links (first 20):')
    for l in links[:20]:
        print(f'  {l}')
