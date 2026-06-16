"""Run EUR/USD + GBP/USD + BTC backtest comparison with current code."""
import sys, json
sys.path.insert(0, r'E:\MyWebProject\CRT_Trading_Bot\CRT_Trading_Bot')
from backtest.backtester import Backtester
from data.forex_loader import ForexDataLoader

loader = ForexDataLoader()
results = []

for pair in ['EUR_USD', 'GBP_USD', 'BTC_USDT']:
    df = loader.load_forex(pair)
    # Limit to same date range for fair comparison
    if pair == 'BTC_USDT':
        df = df[df.index >= '2024-05-15']
    for mode in ['immediate', 'limit_retest']:
        bt = Backtester(
            initial_capital=10000, risk_per_trade=0.02,
            entry_mode=mode, max_leverage=3.0, transaction_cost=10.0,
        )
        r = bt.run(df.copy(), symbol=pair)
        total_pnl = r.get('total_pnl', r.get('net_profit', 0))
        results.append({
            'pair': pair, 'mode': mode,
            'trades': r['total_trades'],
            'win_rate': round(r['win_rate'], 1),
            'pnl': round(total_pnl, 2),
            'pf': round(r.get('profit_factor', 0), 2),
            'sharpe': round(r.get('sharpe_ratio', 0), 2),
            'dd': round(r.get('max_drawdown', 0), 1),
            'avg_win': round(r.get('avg_win', 0), 2),
            'avg_loss': round(r.get('avg_loss', 0), 2),
        })
        print(f"{pair:12s} {mode:15s} trades={r['total_trades']:4d}  WR={r['win_rate']:5.1f}%  PnL=${total_pnl:>8,.0f}  Sharpe={r.get('sharpe_ratio',0):.2f}  DD={r.get('max_drawdown',0):.1f}%")

print("\n--- Summary ---")
header = f"{'Pair':12s} {'Mode':15s} {'Trades':>6s} {'WR':>6s} {'PnL':>10s} {'PF':>6s} {'Sharpe':>7s} {'DD':>6s}"
print(header)
print("-" * len(header))
for r in results:
    print(f"{r['pair']:12s} {r['mode']:15s} {r['trades']:6d} {r['win_rate']:5.1f}% ${r['pnl']:>7,.0f} {r['pf']:5.2f} {r['sharpe']:6.2f} {r['dd']:5.1f}%")

with open('forex_analysis_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nResults saved to forex_analysis_results.json")
