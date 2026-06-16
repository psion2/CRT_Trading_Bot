"""Test histdata.com download flow."""
import requests, re, time

url = 'https://www.histdata.com/download-free-forex-metadata/?/metatrader/15-minute-bar-quotes/EURUSD/2025'
resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'})
print(f'Status: {resp.status_code}, size: {len(resp.text)}')

# Find all download/file links
links = re.findall(r'href=[\"\'](.*?)[\"\']', resp.text)
for l in links[:20]:
    if any(k in l.lower() for k in ['download', 'csv', 'get', '.zip', '.csv', '.gz']):
        print(f'  Download link: {l}')

# Check for form action
forms = re.findall(r'<form[^>]*action=[\"\'](.*?)[\"\']', resp.text)
for f in forms[:5]:
    print(f'  Form action: {f}')

# Check title
titles = re.findall(r'<title>(.*?)</title>', resp.text)
print(f'Page title: {titles[:3]}')

# Show portion of page
if len(resp.text) > 200:
    print(f'\nPage excerpt:\n{resp.text[:200]}')
