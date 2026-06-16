"""Check M15 and M1 availability on histdata."""
import requests, re

for tf_label, tf_param in [('1-minute', 'M1'), ('15-minute', 'M15')]:
    for pair in ['EURUSD', 'GBPUSD', 'XAUUSD', 'XAGUSD']:
        url = f'https://www.histdata.com/download-free-forex-data/?/metatrader/{tf_label}-bar-quotes/{pair}/2025'
        try:
            resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            has_form = 'get.php' in resp.text and 'tk' in resp.text
            tf_in_page = 'M1' if 'timeframe=M1' in resp.text else ('M15' if 'timeframe=M15' in resp.text else '?')
            print(f'{tf_param:>4} {pair}: {resp.status_code} form={has_form} tf_page={tf_in_page}')
        except Exception as e:
            print(f'{tf_param:>4} {pair}: ERROR {str(e)[:30]}')
