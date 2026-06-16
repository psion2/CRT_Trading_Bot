"""Process histdata M1 ZIPs to M15 with better performance."""
import pandas as pd
from pathlib import Path
import zipfile, io

DATA_DIR = Path(__file__).parent / "forex"
MANUAL_DIR = DATA_DIR / "manual_download"

MAPPING = {
    "EURUSD": "EUR_USD",
    "GBPUSD": "GBP_USD",
    "XAUUSD": "XAU_USD",
    "XAGUSD": "XAG_USD",
}

for pair_key, output_name in MAPPING.items():
    out_path = DATA_DIR / f"{output_name}_15m.csv"
    zips = sorted(MANUAL_DIR.glob(f"{pair_key}_*.zip"))
    if not zips:
        print(f"  No ZIPs for {pair_key}, skipping")
        continue
    
    print(f"  Processing {pair_key} ({len(zips)} years)...")
    all_m15 = []
    
    for zf in zips:
        parts = zf.stem.split("_")
        year = parts[1]
        
        try:
            with zipfile.ZipFile(zf, 'r') as z:
                csv_files = [f for f in z.namelist() if f.endswith('.csv') or f.endswith('.CSV')]
                if not csv_files:
                    print(f"    {year}: no CSV in zip")
                    continue
                
                dfs = []
                for cf in csv_files:
                    with z.open(cf) as f:
                        df = pd.read_csv(f, header=None,
                            names=['date', 'time', 'open', 'high', 'low', 'close', 'volume'],
                            dtype={'open': 'float32', 'high': 'float32', 'low': 'float32', 'close': 'float32'})
                        df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%Y.%m.%d %H:%M')
                        df = df[['datetime', 'open', 'high', 'low', 'close']].dropna()
                        df = df.set_index('datetime')
                        dfs.append(df)
                
                if not dfs:
                    continue
                    
                m1 = pd.concat(dfs)
                m1 = m1[~m1.index.duplicated(keep='first')].sort_index()
                
                m15 = m1.resample('15min').agg({
                    'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'
                }).dropna()
                
                all_m15.append(m15)
                print(f"    {year}: {len(m15)} M15 candles (from {len(m1)} M1)")
                
        except Exception as e:
            print(f"    {year}: ERROR: {e}")
    
    if not all_m15:
        print(f"  No data for {pair_key}")
        continue
    
    # Combine all years
    combined = pd.concat(all_m15)
    combined = combined[~combined.index.duplicated(keep='first')].sort_index()
    
    # Merge with existing if present
    if out_path.exists():
        existing = pd.read_csv(out_path, index_col=0, parse_dates=True)
        combined = pd.concat([existing, combined])
        combined = combined[~combined.index.duplicated(keep='first')].sort_index()
    
    combined.to_csv(out_path)
    print(f"  -> {out_path.name}: {len(combined)} candles ({combined.index[0]} to {combined.index[-1]})")

print("\nDone!")
