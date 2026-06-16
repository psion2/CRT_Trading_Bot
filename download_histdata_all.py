"""
Automated download of histdata.com M1 ZIPs via curl_cffi.
Downloads EURUSD, GBPUSD, XAUUSD, XAGUSD for 2016-2025 (2026 not available).
"""
from curl_cffi import requests as curl_requests
import re, os, time, sys

SAVE_DIR = os.path.join(os.path.dirname(__file__), 'data', 'forex', 'manual_download')
os.makedirs(SAVE_DIR, exist_ok=True)

PAIRS = ['EURUSD', 'GBPUSD', 'XAUUSD', 'XAGUSD']
YEARS = [str(y) for y in range(2016, 2027)]  # 2016-2026

session = curl_requests.Session()

def download_one(pair, year):
    """Download single M1 ZIP. Returns True on success."""
    url = f'https://www.histdata.com/download-free-forex-data/?/metatrader/1-minute-bar-quotes/{pair}/{year}'
    fname = f'{pair}_{year}.zip'
    fpath = os.path.join(SAVE_DIR, fname)
    
    if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
        print(f'  [OK] Already exists: {fname} ({os.path.getsize(fpath)} bytes)')
        return True
    
    print(f'  Fetching page for {pair} {year}...')
    resp = session.get(url, impersonate='chrome120')
    if resp.status_code != 200:
        print(f'  [FAIL] Page error: {resp.status_code}')
        return False
    
    html = resp.text
    tk_match = re.search(r'name=["\']tk["\'][^>]*value=["\']([^"\']+)["\']', html)
    if not tk_match:
        print(f'  [FAIL] No token found')
        return False
    tk = tk_match.group(1)
    
    data = {
        'tk': tk,
        'date': year,
        'datemonth': year,
        'platform': 'MT',
        'timeframe': 'M1',
        'fxpair': pair
    }
    
    print(f'  Downloading {pair} {year}...')
    dl = session.post(
        'https://www.histdata.com/get.php',
        data=data,
        impersonate='chrome120',
        headers={'Referer': url},
        timeout=60
    )
    
    if len(dl.content) < 1000 or dl.content[:2] != b'PK':
        print(f'  [FAIL] Invalid/empty response ({len(dl.content)} bytes)')
        return False
    
    with open(fpath, 'wb') as f:
        f.write(dl.content)
    print(f'  [OK] Saved {fname} ({len(dl.content)} bytes)')
    return True

# Download all 12
success = 0
total = len(PAIRS) * len(YEARS)
for i, pair in enumerate(PAIRS, 1):
    for year in YEARS:
        print(f'[{success+1}/{total}] {pair} {year}')
        ok = download_one(pair, year)
        if ok:
            success += 1
        else:
            print(f'  FAILED: {pair} {year}')
        time.sleep(1.5)  # Be polite

print(f'\nDone: {success}/{total} downloaded')
print(f'Saved to: {SAVE_DIR}')
