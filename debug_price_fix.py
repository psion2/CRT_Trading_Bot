"""Debug: print per-trade details for one BTC base config."""
import sys, numpy as np
from pathlib import Path

SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))

from data.forex_loader import ForexDataLoader
from backtest.backtester import Backtester

df = ForexDataLoader().load_forex("BTC_USDT", "4h")
print(f"Loaded BTC/USDT: {len(df)} candles", flush=True)

bt = Backtester(initial_capital=10_000, risk_per_trade=0.02,
    use_kill_zone=False, use_model1=True, use_kod=True, use_ote=True,
    use_breaker_block=True, use_candle3_only=True, use_true_mss=True,
    stop_mode="tsq_trail")

def traced_run(df, symbol, stop_loss_pct=0.015, take_profit_ratios=[1.5, 2.0], ltf_df=None):
    df = bt.strategy.generate_signals(df, ltf_df=ltf_df)
    bt.positions = []
    trade_log = []
    for i in range(len(df)):
        row = df.iloc[i]
        signal = row["signal"]
        current_price = row["close"]
        if signal == 0:
            bt._update_trailing_stops(df, i, current_price)
            bt._check_exits(df, i, current_price, take_profit_ratios)
            continue
        direction = "long" if signal == 1 else "short"
        range_id = int(row.get("crt_range_id", 0))
        inv_price = row.get("crt_inv_price")
        stop_price = row.get("crt_stop_price")
        phase_type = row.get("crt_phase_type", "unknown")
        is_valid = lambda x: x is not None and isinstance(x, (int, float)) and not (isinstance(x, float) and np.isnan(x))
        entry_price = inv_price if is_valid(inv_price) else current_price
        if is_valid(stop_price):
            if direction == "long" and float(stop_price) < entry_price:
                sl = float(stop_price)
            elif direction == "short" and float(stop_price) > entry_price:
                sl = float(stop_price)
            else:
                sl = entry_price * (1 - stop_loss_pct) if direction == "long" else entry_price * (1 + stop_loss_pct)
        else:
            sl = entry_price * (1 - stop_loss_pct) if direction == "long" else entry_price * (1 + stop_loss_pct)
        risk = abs(entry_price - sl)
        if risk <= 0:
            continue
        min_risk = entry_price * stop_loss_pct
        risk_for_sizing = max(risk, min_risk)
        position_size = (bt.risk_manager.capital * bt.risk_per_trade) / risk_for_sizing
        trade = {
            "symbol": symbol, "entry_time": df.index[i], "entry_price": entry_price,
            "direction": direction, "position_size": position_size, "stop_loss": sl,
            "original_sl": sl, "original_risk": risk, "partial_exited": False,
            "status": "open", "range_id": range_id, "phase": phase_type,
        }
        bt.positions.append(trade)
        if len(trade_log) < 5:
            trade_log.append(f"ENT #{len(bt.positions)} idx={i} phase={phase_type} dir={direction} entry={entry_price:.2f} sl={sl:.2f} risk={risk:.2f} risk_sizing={risk_for_sizing:.2f} size={position_size:.6f}")
        bt._update_trailing_stops(df, i, current_price)
        bt._check_exits(df, i, current_price, take_profit_ratios)
    for pos in list(bt.positions):
        if pos["status"] == "open":
            final_price = df.iloc[-1]["close"]
            pnl = bt._calculate_pnl(pos["direction"], pos["entry_price"], final_price, pos["position_size"])
            bt._close_trade(pos, df.index[-1], final_price, pnl, "EOD")
    print("\n--- First 5 entries ---", flush=True)
    for l in trade_log:
        print(l, flush=True)
    closed = [p for p in bt.positions if p["status"] == "closed"]
    wins = [p for p in closed if p.get("pnl", 0) > 0]
    losses = [p for p in closed if p.get("pnl", 0) <= 0]
    print(f"\nTotal: {len(bt.positions)}, Closed: {len(closed)}, Wins: {len(wins)}, Losses: {len(losses)}", flush=True)
    if wins:
        aw = sum(p["pnl"] for p in wins) / len(wins)
        print(f"Avg win: ${aw:.2f}, Max: ${max(p['pnl'] for p in wins):.2f}", flush=True)
    if losses:
        al = sum(p["pnl"] for p in losses) / len(losses)
        print(f"Avg loss: ${al:.2f}, Min: ${min(p['pnl'] for p in losses):.2f}", flush=True)
    print("\n--- Sample closed trades ---", flush=True)
    for p in closed[:5]:
        print(f"  phase={p['phase']} dir={p['direction']} entry={p['entry_price']:.2f} sl={p['stop_loss']:.2f} sz={p['position_size']:.4f} pnl=${p.get('pnl',0):.2f} rsn={p.get('exit_reason','?')}", flush=True)
    return bt._calculate_metrics()

bt.run = traced_run
res = bt.run(df, "BTC/USDT")
print(f"\nTotal PnL: ${res['total_pnl']:.2f}", flush=True)
print(f"Win rate: {res['win_rate']:.1f}%", flush=True)
print(f"Avg win: ${res['avg_win']:.2f}, Avg loss: ${res['avg_loss']:.2f}", flush=True)
