"""Check full histdata get.php response for download URL."""
import requests, re

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html,*/*'})

base = 'https://www.histdata.com'
# GET the page
resp = session.get(f'{base}/download-free-forex-data/?/metatrader/1-minute-bar-quotes/EURUSD/2025', timeout=15)
tk = re.search(r'name=["\']tk["\'][^>]*value=["\']([^"\']+)["\']', resp.text).group(1)

# POST with full headers
data = {'tk': tk, 'date': '2025', 'datemonth': '2025', 'platform': 'MT', 'timeframe': 'M1', 'fxpair': 'EURUSD'}
post_resp = session.post(f'{base}/get.php', data=data, timeout=30,
    headers={
        'Referer': resp.url,
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
    })
print(f'Status: {post_resp.status_code}')
print(f'Headers: {dict(post_resp.headers)}')
print(f'Body: {post_resp.text[:500]}')

# Also try a different approach - maybe it's in the URL
# Check if the token was used to generate a redirect URL
print(f'History: {[r.url for r in post_resp.history]}')
print(f'Cookies: {dict(session.cookies)}')

# Try also with ?download=1 or similar
for ext in ['', '?download=1', '?dl=1']:
    r2 = session.get(f'{base}/get.php{ext}', params=data, timeout=15)
    if len(r2.content) > 0 and r2.content[:2] == b'PK':
        print(f'Got ZIP with {ext}!')
        break
