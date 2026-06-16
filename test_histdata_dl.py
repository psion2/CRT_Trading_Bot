"""Test histdata download flow with session."""
import requests, re, time, io, zipfile

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

# Step 1: GET the download page to get session + token
base = 'https://www.histdata.com'
resp = session.get(f'{base}/download-free-forex-data/?/metatrader/1-minute-bar-quotes/EURUSD/2025', timeout=15)
html = resp.text

# Extract token from form
tk_match = re.search(r'name=["\']tk["\'][^>]*value=["\']([^"\']+)["\']', html)
if not tk_match:
    tk_match = re.search(r'value=["\']([a-f0-9]+)["\'].*?name=["\']tk["\']', html)
tk = tk_match.group(1) if tk_match else None
print(f'Token: {tk}')

# Extract all form actions and inputs
# Find the form for /get.php
get_form = re.search(r'<form[^>]*action=["\']/get\.php["\'][^>]*>(.*?)</form>', html, re.DOTALL)
if get_form:
    inputs = re.findall(r'<input[^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\']', get_form.group(1))
    print(f'get.php form inputs:')
    for name, value in inputs:
        print(f'  {name} = {value}')

# Extract pair from URL
pair_match = re.search(r'/1-minute-bar-quotes/(\w+)/(\d{4})', resp.url)
if pair_match:
    symbol = pair_match.group(1)
    print(f'Symbol from URL: {symbol}')

# Step 2: POST to get.php with form data
if tk:
    form_data = {
        'tk': tk,
        'date': '2025',
        'datemonth': '2025',
        'platform': 'MT',
        'timeframe': 'M1',
        'symbol': 'EURUSD',
        'type': '',  # Might need to figure this out
    }
    print(f'\nPosting to /get.php with: {form_data}')
    post_resp = session.post(f'{base}/get.php', data=form_data, timeout=30)
    print(f'Status: {post_resp.status_code}')
    print(f'Response: {post_resp.text[:300]}')
    
    # If success, we might get a redirect or download URL
    print(f'History: {[r.url for r in post_resp.history]}')
    print(f'Final URL: {post_resp.url}')
    
    # Check if it returned a ZIP file
    if post_resp.status_code == 200 and len(post_resp.content) > 100:
        if post_resp.content[:2] == b'PK':
            print(f'GOT ZIP! Size: {len(post_resp.content)} bytes')
            z = zipfile.ZipFile(io.BytesIO(post_resp.content))
            print(f'ZIP contents: {z.namelist()}')
        else:
            print(f'Response (first 200 chars): {post_resp.text[:200]}')
