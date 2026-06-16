"""Parse histdata page to find download flow."""
import requests, re

url = 'https://www.histdata.com/download-free-forex-data/?/metatrader/1-minute-bar-quotes/EURUSD/2025'
resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
html = resp.text

# Find all forms with their actions and inputs
forms = re.findall(r'<form[^>]*>.*?</form>', html, re.DOTALL)
print(f'Forms found: {len(forms)}')
for i, form in enumerate(forms[:5]):
    action = re.search(r'action=[\"\']([^\"\']*)[\"\']', form)
    inputs = re.findall(r'<input[^>]*>', form)
    print(f'Form {i}: action={action.group(1) if action else "NONE"}, inputs={len(inputs)}')
    for inp in inputs[:5]:
        n = re.search(r'name=[\"\']([^\"\']*)[\"\']', inp)
        v = re.search(r'value=[\"\']([^\"\']*)[\"\']', inp)
        t = re.search(r'type=[\"\']([^\"\']*)[\"\']', inp)
        print(f'  {t.group(1) if t else "?"}: {n.group(1) if n else "?"} = {v.group(1) if v else "?"}')

# Find download button
btns = re.findall(r'<button[^>]*>.*?</button>', html, re.DOTALL)
for b in btns:
    if 'download' in b.lower():
        print(f'Download button: {b[:200]}')

# Find links with "download" text
links = re.findall(r'<a\s+[^>]*>(.*?)</a>', html)
for l in links:
    if 'download' in l.lower():
        print(f'Download link: {l[:200]}')

# Show a snippet around "Download" text
if 'download' in html.lower():
    idx = html.lower().index('download')
    print(f'\nContext around "download":')
    print(html[max(0,idx-200):idx+300])
