"""Complete histdata download flow with proper session."""
import requests, re, time, io, zipfile, pandas as pd

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})
BASE = 'https://www.histdata.com'

def download_m1(pair, year, month=None):
    """Download 1-minute data from histdata.com."""
    # Step 1: GET the page
    month_path = f'/{month}' if month else ''
    url = f'{BASE}/download-free-forex-data/?/metatrader/1-minute-bar-quotes/{pair}/{year}{month_path}'
    resp = session.get(url, timeout=15)
    html = resp.text

    # Step 2: Extract token
    tk = re.search(r'name=["\']tk["\'][^>]*value=["\']([^"\']+)["\']', html)
    if not tk:
        print(f'  No token found')
        return None
    tk = tk.group(1)

    # Step 3: POST to get.php
    form_data = {
        'tk': tk,
        'date': str(year),
        'datemonth': str(year),
        'platform': 'MT',
        'timeframe': 'M1',
        'fxpair': pair,
    }
    post_resp = session.post(f'{BASE}/get.php', data=form_data, timeout=60, headers={'Referer': url})

    if len(post_resp.content) == 0:
        print(f'  Empty response from get.php (file being prepared)')
        return None

    if post_resp.content[:2] == b'PK':
        z = zipfile.ZipFile(io.BytesIO(post_resp.content))
        csv_files = [f for f in z.namelist() if f.endswith('.csv')]
        if csv_files:
            df = pd.read_csv(z.open(csv_files[0]), header=None)
            print(f'  Got CSV: {len(df)} rows')
            return df
    return None

# Test with single month
print('Testing histdata download for EURUSD 2025/1...')
df = download_m1('EURUSD', 2025, 1)
if df is None:
    print('Direct download failed, trying alternative flow...')
    
    # Step 1: GET page
    url = f'{BASE}/download-free-forex-data/?/metatrader/1-minute-bar-quotes/EURUSD/2025'
    resp = session.get(url, timeout=15)
    html = resp.text
    
    # Extract tk
    tk = re.search(r'name=["\']tk["\'][^>]*value=["\']([^"\']+)["\']', html)
    if tk:
        tk = tk.group(1)
        # Try getStatus.php flow
        status_data = {
            'tk': tk,
            'date': '2025',
            'datemonth': '2025',
            'platform': 'MT',
            'timeframe': 'M1',
            'fxpair': 'EURUSD',
        }
        # First check status
        status_resp = session.post(f'{BASE}/getStatus.php', data=status_data, timeout=15)
        print(f'Status response: {status_resp.text[:200]}')
        
        # Then try get
        get_resp = session.post(f'{BASE}/get.php', data=status_data, timeout=60)
        print(f'Get response: {len(get_resp.content)} bytes')
        if len(get_resp.content) > 0:
            if get_resp.content[:2] == b'PK':
                print('Got ZIP!')
                z = zipfile.ZipFile(io.BytesIO(get_resp.content))
                print(f'Files: {z.namelist()}')
            else:
                print(f'First 200 chars: {get_resp.text[:200]}')
