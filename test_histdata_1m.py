"""Try histdata 1-minute data download with session handling."""
import requests, re, time

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

# Different URL patterns for histdata 1M data
patterns = [
    '/download-free-forex-data/?/metatrader/1-minute-bar-quotes/EURUSD/2025',
    '/download-free-forex-data/?/metatrader/1-minute-bar-quotes/EURUSD/2025/1',
    '/download-free-forex-metadata/?/metatrader/1-minute-bar-quotes/EURUSD/2025',
    '/get.php?/metatrader/1-minute-bar-quotes/EURUSD/2025',
    '/dl/?/metatrader/1-minute-bar-quotes/EURUSD/2025',
]

for path in patterns:
    url = f'https://www.histdata.com{path}'
    resp = session.get(url, timeout=15)
    print(f'{resp.status_code} {len(resp.text):>6}B -> {path}')
    if resp.status_code == 200 and len(resp.text) > 100:
        # Check for downloadable content (ZIP/CSV magic bytes)
        is_binary = resp.text[:2] in ['PK', '\x1f\x8b']
        has_dl_link = bool(re.findall(r'href=[\"\']([^\"\']*\.(?:zip|csv|gz))[\"\']', resp.text, re.IGNORECASE))
        print(f'  Binary={is_binary} has_dl_link={has_dl_link}')
        if has_dl_link:
            links = re.findall(r'href=[\"\']([^\"\']*\.(?:zip|csv|gz))[\"\']', resp.text, re.IGNORECASE)
            for l in links[:3]:
                print(f'  DL: {l}')
