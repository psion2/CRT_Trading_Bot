"""Test histdata.com 1-minute data availability and Alpha Vantage 15m."""
import requests, re, sys

# === Test histdata 1M ===
print("=== Histdata 1M Test ===")
for year in [2024, 2025]:
    for pair in ['EURUSD', 'XAUUSD']:
        url = f'https://www.histdata.com/download-free-forex-metadata/?/metatrader/1-minute-bar-quotes/{pair}/{year}'
        resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'})
        # Check for download links
        links = re.findall(r'href=[\"\']([^\"\']*\.(?:zip|csv|gz))[\"\']', resp.text, re.IGNORECASE)
        dl_text = 'DOWNLOAD' in resp.text.upper()
        print(f'  {pair} {year}: status={resp.status_code} size={len(resp.text)} dl_link={len(links)>0} has_dl_text={dl_text}')

# === Test Alpha Vantage ===
print("\n=== Alpha Vantage Test ===")
print("Need your API key to proceed. Run with: python this_script.py YOUR_API_KEY")
