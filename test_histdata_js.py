"""Reverse engineer histdata.com download flow."""
import requests, re

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

# Get the page
url = 'https://www.histdata.com/download-free-forex-data/?/metatrader/1-minute-bar-quotes/EURUSD/2025'
resp = session.get(url, timeout=15)
html = resp.text

# Check for JavaScript that handles download
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
for s in scripts:
    if 'get.php' in s or 'getStatus' in s or 'download' in s.lower() or 'token' in s.lower() or 'tk' in s.lower():
        print(f'Found relevant JS:')
        # Show the relevant portion
        idx = s.lower().find('get.php') if 'get.php' in s else s.lower().find('tk')
        if idx >= 0:
            print(s[max(0,idx-100):idx+300])
        print('---')

# Check for data attributes
data_atts = re.findall(r'data-[a-z]+=[\"\'][^\"\']*[\"\']', html)
for d in data_atts[:20]:
    print(f'Data attr: {d}')

# Check specific div/button for download
dl_btn = re.search(r'<button[^>]*class=[\"\'][^\"\']*dl[^\"\']*[\"\']', html)
if dl_btn:
    print(f'Download button: {dl_btn.group()[:200]}')

# Look for onclick handlers
onclicks = re.findall(r'onclick=[\"\']([^\"\']*)[\"\']', html)
for oc in onclicks:
    if 'download' in oc.lower() or 'get' in oc.lower():
        print(f'Onclick: {oc[:200]}')
