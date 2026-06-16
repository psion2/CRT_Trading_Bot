"""Quick comparison: old results vs current."""
import sys; from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

loader = ForexDataLoader()
old = {("BTC/USDT","Base"):(1374,91198.47),("BTC/USDT","M1_Only"):(570,617.69),
       ("ETH/USDT","Base"):(1360,66266.26),("ETH/USDT","M1_Only"):(550,2321.71),
       ("EUR/USD","Base"):(775,79896.33),("EUR/USD","M1_Only"):(369,3638.84)}

for p,r in [("BTC/USDT","BTC_USDT"),("ETH/USDT","ETH_USDT"),("EUR/USD","EUR_USD")]:
    df = loader.load_forex(r,"4h")
    if df.index.tz is not None: df.index = df.index.tz_localize(None)
    for cfg in [("Base",0,1,1,1,1,1,1),("M1_Only",0,1,0,0,0,1,0)]:
        bt = Backtester(10000,0.02,bool(cfg[1]),bool(cfg[2]),bool(cfg[3]),bool(cfg[4]),bool(cfg[5]),bool(cfg[6]),bool(cfg[7]),"tsq_trail")
        r = bt.run(df,p,0.015,[1.5,2.0])
        o = old.get((p,cfg[0]))
        d = f"({((r['total_pnl']/o[1])-1)*100:+.0f}%)" if o else ""
        print(f"{p:<10} {cfg[0]:<8} trades={r['total_trades']:<5} PnL=${r['total_pnl']:<+9.2f} WR={r['win_rate']:<5.1f} old_trades={o[0] if o else '?'} old_PnL=${o[1] if o else 0:<+9.2f} {d}")
