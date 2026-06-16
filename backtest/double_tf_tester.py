"""
Double Timeframe Pipeline Tester (HTF -> LTF)
Test HTF bias + LTF execution without ITF
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from data.data_fetcher import DataFetcher
from backtest.backtester import Backtester
import warnings
warnings.filterwarnings('ignore')


# Double Timeframe Pipelines
DOUBLE_TF_PIPELINES = [
    {'name': 'Weekly->4H', 'htf': '1w', 'ltf': '4h', 'months': 24},
    {'name': 'Daily->1H', 'htf': '1d', 'ltf': '1h', 'months': 12},
    {'name': '4H->15m', 'htf': '4h', 'ltf': '15m', 'months': 6},
    {'name': 'Daily->4H', 'htf': '1d', 'ltf': '4h', 'months': 12},
]


# Signal configurations
SIGNAL_CONFIGS = [
    {'name': 'KOD', 'kod': True, 'm1': False, 'ote': False, 'bb': False},
    {'name': 'Model-1', 'kod': False, 'm1': True, 'ote': False, 'bb': False},
    {'name': 'OTE', 'kod': False, 'm1': False, 'ote': True, 'bb': False},
    {'name': 'BB', 'kod': False, 'm1': False, 'ote': False, 'bb': True},
    {'name': 'KOD+Model1', 'kod': True, 'm1': True, 'ote': False, 'bb': False},
    {'name': 'KOD+OTE', 'kod': True, 'm1': False, 'ote': True, 'bb': False},
    {'name': 'KOD+BB', 'kod': True, 'm1': False, 'ote': False, 'bb': True},
    {'name': 'Model1+OTE', 'kod': False, 'm1': True, 'ote': True, 'bb': False},
    {'name': 'Model1+BB', 'kod': False, 'm1': True, 'ote': False, 'bb': True},
    {'name': 'All', 'kod': True, 'm1': True, 'ote': True, 'bb': True},
]


def fetch_htf_data(fetcher, symbol, htf_tf, months):
    """Fetch and calculate HTF bias."""
    now = pd.Timestamp('2026-05-16')
    since = int((now - pd.DateOffset(months=months)).timestamp() * 1000)

    try:
        htf_df = fetcher.fetch_ohlcv(symbol, htf_tf, since=since, limit=200)
        if len(htf_df) < 5:
            return None

        # Calculate bias: recent close vs earlier close
        recent = htf_df['close'].iloc[-1]
        earlier = htf_df['close'].iloc[-min(5, len(htf_df))]
        bias = 1 if recent > earlier else (-1 if recent < earlier else 0)

        return bias
    except:
        return None


def run_double_tf_test(symbol, pipeline, signal_cfg, use_filters=True):
    """Test HTF -> LTF pipeline with specific signal config."""
    fetcher = DataFetcher()
    now = pd.Timestamp('2026-05-16')
    since = int((now - pd.DateOffset(months=pipeline['months'])).timestamp() * 1000)

    # Fetch LTF data (main execution timeframe)
    try:
        ltf_df = fetcher.fetch_ohlcv(symbol, pipeline['ltf'], since=since, limit=4000)
        if len(ltf_df) < 20:
            return None
    except:
        return None

    # Get HTF for bias filtering (optional)
    htf_bias = fetch_htf_data(fetcher, symbol, pipeline['htf'], pipeline['months'])

    # Run backtest
    if use_filters:
        bt = Backtester(
            initial_capital=10_000,
            risk_per_trade=0.03,
            use_kill_zone=True,
            use_market_profile=True,
            use_time_theory=False,
            use_kod=signal_cfg['kod'],
            use_model1=signal_cfg['m1'],
            use_ote=signal_cfg['ote'],
            use_breaker_block=signal_cfg['bb'],
        )
    else:
        bt = Backtester(
            initial_capital=10_000,
            risk_per_trade=0.03,
            use_kill_zone=False,
            use_market_profile=False,
            use_time_theory=False,
            use_kod=signal_cfg['kod'],
            use_model1=signal_cfg['m1'],
            use_ote=signal_cfg['ote'],
            use_breaker_block=signal_cfg['bb'],
        )

    result = bt.run(ltf_df, symbol)

    return {
        'pipeline': pipeline['name'],
        'htf': pipeline['htf'],
        'ltf': pipeline['ltf'],
        'signal': signal_cfg['name'],
        'trades': result['total_trades'],
        'win_rate': result['win_rate'],
        'pnl': result['total_pnl'],
        'profit_factor': result['profit_factor'],
        'max_dd': result['max_drawdown'],
        'htf_bias': htf_bias,
    }


def run_all_tests():
    """Run all double TF pipeline tests."""
    symbols = ['BTC/USDT', 'ETH/USDT']

    print("="*100)
    print("DOUBLE TIMEFRAME PIPELINE TESTER (HTF -> LTF)")
    print("="*100)
    print()

    results = []

    for symbol in symbols:
        print(f"\n{'='*60}")
        print(f"SYMBOL: {symbol}")
        print(f"{'='*60}")

        for pipeline in DOUBLE_TF_PIPELINES:
            print(f"\n--- {pipeline['name']} ---")

            for signal_cfg in SIGNAL_CONFIGS:
                # Test without filters
                r1 = run_double_tf_test(symbol, pipeline, signal_cfg, use_filters=False)
                if r1 and r1['trades'] > 0:
                    print(f"  {signal_cfg['name']} (No Filt): {r1['trades']} trades, Win {r1['win_rate']:.0f}%, PnL ${r1['pnl']:.0f}, PF {r1['profit_factor']:.1f}")
                    results.append({**r1, 'symbol': symbol, 'filters': 'None'})

                # Test with filters
                r2 = run_double_tf_test(symbol, pipeline, signal_cfg, use_filters=True)
                if r2 and r2['trades'] > 0:
                    print(f"  {signal_cfg['name']} (KZ+MP): {r2['trades']} trades, Win {r2['win_rate']:.0f}%, PnL ${r2['pnl']:.0f}, PF {r2['profit_factor']:.1f}")
                    results.append({**r2, 'symbol': symbol, 'filters': 'KZ+MP'})

    return results


def summarize_results(results):
    """Summarize test results."""
    if not results:
        print("No results!")
        return

    df = pd.DataFrame(results)

    print("\n" + "="*100)
    print("SUMMARY BY PIPELINE")
    print("="*100)

    summary = df.groupby('pipeline').agg({
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

    df_pos = df[df['pnl'] > 0].copy()
    df_pos['score'] = df_pos['trades'] * df_pos['win_rate'] * df_pos['profit_factor'] / (df_pos['max_dd'] + 1)
    df_pos = df_pos.sort_values('score', ascending=False).head(20)

    print(df_pos[['symbol', 'pipeline', 'signal', 'filters', 'trades', 'win_rate', 'pnl', 'profit_factor']].to_string())


if __name__ == "__main__":
    print("Running double timeframe pipeline tests...")
    print("Testing HTF -> LTF (no ITF) with all signal combinations...")
    print()

    results = run_all_tests()
    summarize_results(results)