"""
Full Permutation Tester - All Signal + Filter Combinations
4H -> 15m Pipeline, 2 Years (PROPER HTF->LTF IMPLEMENTATION)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from data.data_fetcher import DataFetcher
from backtest.backtester import Backtester
import warnings
warnings.filterwarnings('ignore')


# All Signal Combinations
SIGNAL_CONFIGS = [
    {'name': 'KOD', 'kod': True, 'm1': False, 'ote': False, 'bb': False},
    {'name': 'Model-1', 'kod': False, 'm1': True, 'ote': False, 'bb': False},
    {'name': 'OTE', 'kod': False, 'm1': False, 'ote': True, 'bb': False},
    {'name': 'BB', 'kod': False, 'm1': False, 'ote': False, 'bb': True},
    {'name': 'KOD+Model1', 'kod': True, 'm1': True, 'ote': False, 'bb': False},
    {'name': 'KOD+OTE', 'kod': True, 'm1': False, 'ote': True, 'bb': False},
    {'name': 'Model1+OTE', 'kod': False, 'm1': True, 'ote': True, 'bb': False},
    {'name': 'KOD+BB', 'kod': True, 'm1': False, 'ote': False, 'bb': True},
    {'name': 'Model1+BB', 'kod': False, 'm1': True, 'ote': False, 'bb': True},
    {'name': 'All', 'kod': True, 'm1': True, 'ote': True, 'bb': True},
]


# All Filter Combinations
FILTER_CONFIGS = [
    {'name': 'None', 'kz': False, 'mp': False, 'tt': False},
    {'name': 'KZ', 'kz': True, 'mp': False, 'tt': False},
    {'name': 'MP', 'kz': False, 'mp': True, 'tt': False},
    {'name': 'TT', 'kz': False, 'mp': False, 'tt': True},
    {'name': 'KZ+MP', 'kz': True, 'mp': True, 'tt': False},
    {'name': 'KZ+TT', 'kz': True, 'mp': False, 'tt': True},
    {'name': 'MP+TT', 'kz': False, 'mp': True, 'tt': True},
    {'name': 'KZ+MP+TT', 'kz': True, 'mp': True, 'tt': True},
]


def fetch_htf_data(fetcher, symbol, htf_tf, months):
    """Fetch HTF data for signal detection."""
    now = pd.Timestamp('2026-05-17')
    since = int((now - pd.DateOffset(months=months)).timestamp() * 1000)

    try:
        htf_df = fetcher.fetch_ohlcv(symbol, htf_tf, since=since, limit=4000)
        return htf_df
    except Exception as e:
        print(f"Error fetching HTF ({htf_tf}): {e}")
        return None


def fetch_ltf_data(fetcher, symbol, ltf_tf, months):
    """Fetch LTF data for execution."""
    now = pd.Timestamp('2026-05-17')
    since = int((now - pd.DateOffset(months=months)).timestamp() * 1000)

    try:
        ltf_df = fetcher.fetch_ohlcv(symbol, ltf_tf, since=since, limit=8000)
        return ltf_df
    except Exception as e:
        print(f"Error fetching LTF ({ltf_tf}): {e}")
        return None


def run_full_test():
    """Run all permutations with proper HTF->LTF pipeline."""
    symbols = ['BTC/USDT', 'ETH/USDT']
    htf_tf = '4h'  # Signal detection timeframe
    ltf_tf = '15m'  # Execution timeframe
    months = 24  # 2 years

    # Calculate since timestamp
    now = pd.Timestamp('2026-05-17')
    since = int((now - pd.DateOffset(months=months)).timestamp() * 1000)

    print("="*100)
    print("FULL PERMUTATION TEST - 4H->15m Pipeline (FIXED)")
    print("Testing: 10 Signals x 8 Filters x 2 Symbols = 160 combinations")
    print("HTF: 4H (signal detection) -> LTF: 15m (execution)")
    print("="*100)
    print()

    results = []
    count = 0

    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"SYMBOL: {symbol}")
        print(f"{'='*60}")

        # Fetch HTF data (4H) for signal detection
        fetcher = DataFetcher()
        htf_df = fetcher.fetch_ohlcv(symbol, htf_tf, since=since, limit=4000)

        if htf_df is None or len(htf_df) < 20:
            print(f"Error: Could not load 4H data for {symbol}")
            continue

        print(f"HTF (4H): {len(htf_df)} candles loaded")

        # Fetch LTF data (15m) for execution
        ltf_df = fetcher.fetch_ohlcv(symbol, ltf_tf, since=since, limit=10000)

        if ltf_df is None or len(ltf_df) < 20:
            print(f"Error: Could not load 15m data for {symbol}")
            continue

        print(f"LTF (15m): {len(ltf_df)} candles loaded")

        for sig_cfg in SIGNAL_CONFIGS:
            for filt_cfg in FILTER_CONFIGS:
                count += 1

                # Run backtest with proper HTF->LTF pipeline
                bt = Backtester(
                    initial_capital=10_000,
                    risk_per_trade=0.03,
                    use_kill_zone=filt_cfg['kz'],
                    use_market_profile=filt_cfg['mp'],
                    use_time_theory=filt_cfg['tt'],
                    use_kod=sig_cfg['kod'],
                    use_model1=sig_cfg['m1'],
                    use_ote=sig_cfg['ote'],
                    use_breaker_block=sig_cfg['bb'],
                )

                # Pass HTF as main df (signals), LTF as ltf_df (execution)
                r = bt.run(htf_df, symbol, ltf_df=ltf_df)

                if r['total_trades'] > 0:
                    print(f"  {sig_cfg['name']} + {filt_cfg['name']}: {r['total_trades']} trades, Win {r['win_rate']:.0f}%, PnL ${r['total_pnl']:.0f}, PF {r['profit_factor']:.1f}")

                    results.append({
                        'symbol': symbol,
                        'signal': sig_cfg['name'],
                        'filter': filt_cfg['name'],
                        'trades': r['total_trades'],
                        'win_rate': r['win_rate'],
                        'pnl': r['total_pnl'],
                        'profit_factor': r['profit_factor'],
                        'max_dd': r['max_drawdown'],
                    })

    return results


def summarize(results):
    """Summarize results."""
    if not results:
        print("No results!")
        return

    df = pd.DataFrame(results)

    print("\n" + "="*100)
    print("SUMMARY BY SIGNAL TYPE")
    print("="*100)

    sig_summary = df.groupby('signal').agg({
        'trades': 'mean',
        'win_rate': 'mean',
        'pnl': 'sum',
        'profit_factor': 'mean',
    }).round(2)
    sig_summary = sig_summary.sort_values('pnl', ascending=False)
    print(sig_summary.to_string())

    print("\n" + "="*100)
    print("SUMMARY BY FILTER")
    print("="*100)

    filt_summary = df.groupby('filter').agg({
        'trades': 'mean',
        'win_rate': 'mean',
        'pnl': 'sum',
        'profit_factor': 'mean',
    }).round(2)
    filt_summary = filt_summary.sort_values('pnl', ascending=False)
    print(filt_summary.to_string())

    print("\n" + "="*100)
    print("TOP 30 BEST CONFIGURATIONS")
    print("="*100)

    df_pos = df[df['pnl'] > 0].copy()
    df_pos['score'] = df_pos['trades'] * df_pos['win_rate'] * df_pos['profit_factor'] / (df_pos['max_dd'] + 1)
    df_pos = df_pos.sort_values('pnl', ascending=False).head(30)

    print(df_pos[['symbol', 'signal', 'filter', 'trades', 'win_rate', 'pnl', 'profit_factor', 'max_dd']].to_string())


if __name__ == "__main__":
    print("Running FULL permutation test with PROPER 4H->15m pipeline...")
    print("Signals detected on 4H, executed on 15m")
    print()

    results = run_full_test()
    summarize(results)