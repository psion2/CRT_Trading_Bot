"""Check what histdata returned."""
import requests, re

url = 'https://www.histdata.com/download-free-forex-data/?/metatrader/15-minute-bar-quotes/EURUSD/2025/5'
resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})

links = re.findall(r'href=[\"\'](.*?)[\"\']', resp.text)
for l in links:
    if any(k in l.lower() for k in ['download', 'csv', 'zip', 'gz', 'get']):
        print(f'Link: {l}')

forms = re.findall(r'<form[^>]*action=[\"\'](.*?)[\"\']', resp.text)
for f in forms:
    print(f'Form action: {f}')

titles = re.findall(r'<title>(.*?)</title>', resp.text)
print(f'Title: {titles}')

# Look for actual download button/text
if 'download' in resp.text.lower():
    idx = resp.text.lower().index('download')
    print(f'First "download" at {idx}')
    print(f'Context: {resp.text[max(0,idx-50):idx+200]}')
