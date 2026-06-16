"""
Signal Type Combination Tester
Tests all permutations of KOD, Model-1, OTE, Breaker Block signal types
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from itertools import combinations
from data.data_fetcher import DataFetcher
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester
import warnings
warnings.filterwarnings('ignore')


# All signal types
SIGNAL_TYPES = {
    'kod': 'KOD (Kiss of Death)',
    'model1': 'Model-1',
    'ote': 'OTE (60-75% Zone)',
    'breaker_block': 'Breaker Block',
}

# Symbols to test
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'SOL/USDT', 'EUR_USD', 'GBP_USD']

# Time periods
PERIODS = {'6 Months': 6, '1 Year': 12, '2 Years': 24}


def get_signal_combinations():
    """Generate all signal type combinations."""
    signal_names = list(SIGNAL_TYPES.keys())
    combos = []

    # Single signals
    for s in signal_names:
        combos.append({s: True})

    # Double combinations
    for combo in combinations(signal_names, 2):
        combos.append({c: True for c in combo})

    # Triple combinations
    for combo in combinations(signal_names, 3):
        combos.append({c: True for c in combo})

    # All four
    combos.append({s: True for s in signal_names})

    # Also test all off (baseline)
    combos.insert(0, {})

    return combos


def run_test(symbol: str, months: int, filters: dict, signals: dict) -> dict:
    """Run backtest for single config."""
    # Handle crypto vs forex
    if '_' in symbol and '/' not in symbol:
        # Forex
        loader = ForexDataLoader()
        try:
            df = loader.load_forex(symbol)
        except:
            return None
    else:
        # Crypto
        fetcher = DataFetcher()
        now = pd.Timestamp('2026-05-16')
        since = int((now - pd.DateOffset(months=months)).timestamp() * 1000)
        try:
            df = fetcher.fetch_ohlcv(symbol, '4h', since=since, limit=2000)
            if len(df) < 50:
                return None
        except:
            return None

    bt = Backtester(
        initial_capital=10_000,
        risk_per_trade=0.03,
        use_kill_zone=filters.get('kill_zone', False),
        use_market_profile=filters.get('market_profile', False),
        use_time_theory=filters.get('time_theory', False),
        use_kod=signals.get('kod', True),
        use_model1=signals.get('model1', True),
        use_ote=signals.get('ote', True),
        use_breaker_block=signals.get('breaker_block', True),
    )

    r = bt.run(df, symbol, take_profit_ratios=[1.5, 2.0])

    # Calculate R:R
    avg_win = r.get('avg_win', 0)
    avg_loss = abs(r.get('avg_loss', 1))
    rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0

    return {
        'trades': r['total_trades'],
        'win_rate': r['win_rate'],
        'pnl': r['total_pnl'],
        'profit_factor': r['profit_factor'],
        'max_dd': r['max_drawdown'],
        'rr_ratio': rr_ratio,
    }


def run_comprehensive_test():
    """Run all signal combination tests."""
    signal_combos = get_signal_combinations()
    filter_configs = [
        {'name': 'No Filters', 'kill_zone': False, 'market_profile': False, 'time_theory': False},
        {'name': 'Kill Zone', 'kill_zone': True, 'market_profile': False, 'time_theory': False},
        {'name': 'MP + TT', 'kill_zone': False, 'market_profile': True, 'time_theory': True},
        {'name': 'KZ + MP + TT', 'kill_zone': True, 'market_profile': True, 'time_theory': True},
    ]

    print("="*100)
    print("SIGNAL TYPE COMBINATION TESTER")
    print("="*100)
    print()

    results = []

    # Test each symbol
    for symbol in SYMBOLS:
        print(f"\n{'='*60}")
        print(f"SYMBOL: {symbol}")
        print(f"{'='*60}")

        for period_name, months in [('6M', 6), ('1Y', 12)]:
            print(f"\n--- {period_name} ---")

            for sig_combo in signal_combos:
                sig_names = ', '.join(sig_combo.keys()) if sig_combo else 'NO SIGNALS'

                for filt in filter_configs:
                    result = run_test(symbol, months, filt, sig_combo)

                    if result and result['trades'] > 0:
                        print(f"  {sig_names} + {filt['name']}")
                        print(f"    Trades: {result['trades']}, Win: {result['win_rate']:.0f}%, PnL: ${result['pnl']:.0f}, PF: {result['profit_factor']:.1f}, DD: {result['max_dd']:.1f}%")

                        results.append({
                            'symbol': symbol,
                            'period': period_name,
                            'signals': sig_names,
                            'filters': filt['name'],
                            **result,
                        })

    return results


def summarize_results(results):
    """Create summary of results."""
    if not results:
        print("No results to summarize!")
        return

    df = pd.DataFrame(results)

    print("\n" + "="*100)
    print("SUMMARY BY SIGNAL COMBINATION")
    print("="*100)

    summary = df.groupby('signals').agg({
        'trades': 'mean',
        'win_rate': 'mean',
        'pnl': 'sum',
        'profit_factor': 'mean',
        'max_dd': 'mean',
    }).round(2)

    summary = summary.sort_values('pnl', ascending=False)
    print(summary.to_string())

    print("\n" + "="*100)
    print("BEST CONFIGURATIONS (Top 20)")
    print("="*100)

    # Filter to positive PnL
    df_pos = df[df['pnl'] > 0].copy()
    df_pos['score'] = df_pos['win_rate'] * df_pos['profit_factor'] / (df_pos['max_dd'] + 1)
    df_pos = df_pos.sort_values('score', ascending=False).head(20)

    print(df_pos[['symbol', 'period', 'signals', 'filters', 'trades', 'win_rate', 'pnl', 'profit_factor', 'max_dd']].to_string())


if __name__ == "__main__":
    print("Running comprehensive signal tests...")
    print("This may take several minutes...")
    print()

    results = run_comprehensive_test()
    summarize_results(results)