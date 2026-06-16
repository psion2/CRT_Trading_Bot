"""
Comprehensive Filter Testing for CRT Strategy
Tests all filter combinations across different time periods and symbols
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from itertools import combinations
from data.data_fetcher import DataFetcher
from backtest.backtester import Backtester
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')


# All filters available
FILTERS = {
    'kill_zone': 'Kill Zone (London/NY sessions)',
    'market_profile': 'Market Profile (filter ranging)',
    'time_theory': 'Time Theory (filter low prob days)',
}

# All symbols to test
SYMBOLS = [
    # Crypto
    'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT',
    # Forex
    'EUR/USDT', 'GBP/USDT', 'AUD/USDT',
]

# Time periods
PERIODS = {
    '6 Months': 6,
    '1 Year': 12,
    '2 Years': 24,
}

# Generate all filter combinations
def get_all_filter_combinations():
    """Generate all possible filter combinations."""
    filter_names = list(FILTERS.keys())
    combinations_list = []

    # Single filters
    for f in filter_names:
        combinations_list.append({f: True})

    # Double filters
    for combo in combinations(filter_names, 2):
        combos_dict = {f: True for f in combo}
        combinations_list.append(combos_dict)

    # Triple filters
    if len(filter_names) >= 3:
        combos_dict = {f: True for f in filter_names}
        combinations_list.append(combos_dict)

    # Also add "no filters" option
    combinations_list.insert(0, {})

    return combinations_list


def run_test(symbol: str, months: int, filters: Dict) -> Dict:
    """Run backtest for a single config."""
    fetcher = DataFetcher()
    now = pd.Timestamp('2026-05-16')
    since = int((now - pd.DateOffset(months=months)).timestamp() * 1000)

    try:
        df = fetcher.fetch_ohlcv(symbol, '4h', since=since, limit=2000)
        if len(df) < 50:
            return None
    except Exception as e:
        return None

    bt = Backtester(
        initial_capital=10_000,
        risk_per_trade=0.03,
        use_kill_zone=filters.get('kill_zone', False),
        use_market_profile=filters.get('market_profile', False),
        use_time_theory=filters.get('time_theory', False),
    )

    r = bt.run(df, symbol, take_profit_ratios=[1.5, 2.0])

    # Calculate R:R (average win / average loss)
    avg_win = r.get('avg_win', 0)
    avg_loss = abs(r.get('avg_loss', 1))
    rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0

    return {
        'trades': r['total_trades'],
        'win_rate': r['win_rate'],
        'pnl': r['total_pnl'],
        'profit_factor': r['profit_factor'],
        'max_dd': r['max_drawdown'],
        'sharpe': r['sharpe_ratio'],
        'rr_ratio': rr_ratio,
        'avg_win': avg_win,
        'avg_loss': -avg_loss,
    }


def run_comprehensive_test():
    """Run all filter combinations across all periods and symbols."""
    filter_combos = get_all_filter_combinations()

    print("="*100)
    print("COMPREHENSIVE FILTER TESTING - CRT STRATEGY")
    print("="*100)

    all_results = []

    for period_name, months in PERIODS.items():
        print(f"\n{'='*50}")
        print(f"PERIOD: {period_name.upper()}")
        print(f"{'='*50}")

        for symbol in SYMBOLS:
            print(f"\n--- {symbol} ---")

            for filters in filter_combos:
                filter_names = ', '.join(filters.keys()) if filters else 'NO FILTERS'

                result = run_test(symbol, months, filters)
                if result is None:
                    continue

                r = result

                # Only show if trades > 0
                if r['trades'] > 0:
                    print(f"  {filter_names}")
                    print(f"    Trades: {r['trades']}, Win: {r['win_rate']:.0f}%, PnL: ${r['pnl']:.0f}, PF: {r['profit_factor']:.1f}, DD: {r['max_dd']:.1f}%, RR: {r['rr_ratio']:.1f}")

                    all_results.append({
                        'period': period_name,
                        'symbol': symbol,
                        'filters': filter_names,
                        **r,
                    })

    return all_results


def find_best_configs(results: List[Dict]) -> pd.DataFrame:
    """Find best performing configurations."""
    df = pd.DataFrame(results)

    # Filter out configs with no trades or negative PnL
    df = df[df['trades'] > 0]
    df = df[df['pnl'] > 0]

    # Sort by a composite score: win_rate * profit_factor / max_dd
    df['score'] = df['win_rate'] * df['profit_factor'] / (df['max_dd'] + 1)

    df = df.sort_values('score', ascending=False)

    return df.head(30)


def create_summary_table(results: List[Dict]) -> pd.DataFrame:
    """Create summary by filter combination."""
    df = pd.DataFrame(results)

    summary = df.groupby('filters').agg({
        'trades': 'mean',
        'win_rate': 'mean',
        'pnl': 'sum',
        'profit_factor': 'mean',
        'max_dd': 'mean',
        'rr_ratio': 'mean',
    }).round(2)

    summary = summary.sort_values('pnl', ascending=False)

    return summary


if __name__ == "__main__":
    print("Running comprehensive filter tests...")
    print("This may take several minutes...")

    results = run_comprehensive_test()

    print("\n" + "="*100)
    print("TOP PERFORMING CONFIGURATIONS")
    print("="*100)

    best = find_best_configs(results)
    print(best[['period', 'symbol', 'filters', 'trades', 'win_rate', 'pnl', 'profit_factor', 'max_dd', 'rr_ratio']].to_string())

    print("\n" + "="*100)
    print("SUMMARY BY FILTER COMBINATION")
    print("="*100)

    summary = create_summary_table(results)
    print(summary.to_string())