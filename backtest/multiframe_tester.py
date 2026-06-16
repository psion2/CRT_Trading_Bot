"""
Multi-Timeframe Alignment Tester
Tests HTF → ITF → LTF pipeline across different timeframe alignments
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from data.data_fetcher import DataFetcher
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester
import warnings
warnings.filterwarnings('ignore')


# Timeframe Alignment Chains
ALIGNMENT_CHAINS = [
    {'name': 'Weekly->Daily->4H', 'htf': '1w', 'itf': '1d', 'ltf': '4h', 'months': 24},
    {'name': 'Daily->4H->1H', 'htf': '1d', 'itf': '4h', 'ltf': '1h', 'months': 12},
    {'name': '4H->1H->15m', 'htf': '4h', 'itf': '1h', 'ltf': '15m', 'months': 6},
    {'name': '1H->15m->5m', 'htf': '1h', 'itf': '15m', 'ltf': '5m', 'months': 3},
]


def fetch_htf_bias(fetcher, symbol, htf_timeframe, months):
    """Fetch HTF data and calculate bias."""
    now = pd.Timestamp('2026-05-16')
    since = int((now - pd.DateOffset(months=months)).timestamp() * 1000)

    try:
        htf_df = fetcher.fetch_ohlcv(symbol, htf_timeframe, since=since, limit=200)
        if len(htf_df) < 10:
            return None, None

        # Calculate bias: compare recent close to earlier close
        if len(htf_df) >= 5:
            recent = htf_df['close'].iloc[-1]
            earlier = htf_df['close'].iloc[-5]
            bias = 1 if recent > earlier else (-1 if recent < earlier else 0)
        else:
            bias = 0

        return htf_df, bias
    except Exception as e:
        return None, None


def run_alignment_test(symbol, chain, use_filters=True, use_ltf=True):
    """Test a specific timeframe alignment chain."""
    fetcher = DataFetcher()
    now = pd.Timestamp('2026-05-16')
    since = int((now - pd.DateOffset(months=chain['months'])).timestamp() * 1000)

    try:
        # Fetch ITF data (main signal timeframe)
        itf_df = fetcher.fetch_ohlcv(symbol, chain['itf'], since=since, limit=3000)
        if len(itf_df) < 20:
            return None
    except Exception as e:
        return None

    # Get HTF data for bias
    htf_df, htf_bias = fetch_htf_bias(fetcher, symbol, chain['htf'], chain['months'])

    # Get LTF data for execution confirmation
    ltf_df = None
    if use_ltf:
        try:
            ltf_df = fetcher.fetch_ohlcv(symbol, chain['ltf'], since=since, limit=4000)
        except:
            pass

    # Run backtest with filters
    if use_filters:
        bt = Backtester(
            initial_capital=10_000,
            risk_per_trade=0.03,
            use_kill_zone=True,
            use_market_profile=True,
            use_time_theory=False,
        )
    else:
        bt = Backtester(
            initial_capital=10_000,
            risk_per_trade=0.03,
            use_kill_zone=False,
            use_market_profile=False,
            use_time_theory=False,
        )

    result = bt.run(itf_df, symbol, ltf_df=ltf_df)

    return {
        'htf': chain['htf'],
        'itf': chain['itf'],
        'ltf': chain['ltf'],
        'trades': result['total_trades'],
        'win_rate': result['win_rate'],
        'pnl': result['total_pnl'],
        'profit_factor': result['profit_factor'],
        'max_dd': result['max_drawdown'],
        'htf_bias': htf_bias,
    }


def run_all_tests():
    """Run all alignment chain tests."""
    symbols = ['BTC/USDT', 'ETH/USDT']

    print("="*100)
    print("MULTI-TIMEFRAME ALIGNMENT TESTER")
    print("="*100)
    print()

    results = []

    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"SYMBOL: {symbol}")
        print(f"{'='*60}")

        for chain in ALIGNMENT_CHAINS:
            print(f"\n--- {chain['name']} ({chain['months']} months) ---")

            # Test without filters
            r1 = run_alignment_test(symbol, chain, use_filters=False, use_ltf=False)
            if r1:
                print(f"  No Filters: {r1['trades']} trades, Win {r1['win_rate']:.0f}%, PnL ${r1['pnl']:.0f}, PF {r1['profit_factor']:.1f}")
                results.append({**r1, 'symbol': symbol, 'filters': 'None', 'chain_name': chain['name']})

            # Test with filters
            r2 = run_alignment_test(symbol, chain, use_filters=True, use_ltf=False)
            if r2:
                print(f"  With Filters: {r2['trades']} trades, Win {r2['win_rate']:.0f}%, PnL ${r2['pnl']:.0f}, PF {r2['profit_factor']:.1f}")
                results.append({**r2, 'symbol': symbol, 'filters': 'KZ+MP', 'chain_name': chain['name']})

            # Test with filters + LTF
            r3 = run_alignment_test(symbol, chain, use_filters=True, use_ltf=True)
            if r3:
                print(f"  KZ+MP+LTF: {r3['trades']} trades, Win {r3['win_rate']:.0f}%, PnL ${r3['pnl']:.0f}, PF {r3['profit_factor']:.1f}")
                results.append({**r3, 'symbol': symbol, 'filters': 'KZ+MP+LTF', 'chain_name': chain['name']})

    return results


def summarize_results(results):
    """Summarize test results."""
    if not results:
        print("No results!")
        return

    df = pd.DataFrame(results)

    print("\n" + "="*100)
    print("SUMMARY BY ALIGNMENT CHAIN")
    print("="*100)

    summary = df.groupby('chain_name').agg({
        'trades': 'mean',
        'win_rate': 'mean',
        'pnl': 'sum',
        'profit_factor': 'mean',
        'max_dd': 'mean',
    }).round(2)

    summary = summary.sort_values('pnl', ascending=False)
    print(summary.to_string())

    print("\n" + "="*100)
    print("BEST CONFIGURATIONS (Top 10)")
    print("="*100)

    df_pos = df[df['pnl'] > 0].copy()
    df_pos = df_pos.sort_values('pnl', ascending=False).head(10)
    print(df_pos[['symbol', 'chain_name', 'filters', 'trades', 'win_rate', 'pnl', 'profit_factor']].to_string())


if __name__ == "__main__":
    print("Running multi-timeframe alignment tests...")
    print("Testing BTC & ETH across all timeframe chains...")
    print()

    results = run_all_tests()
    summarize_results(results)