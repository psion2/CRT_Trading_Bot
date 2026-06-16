from flask import Blueprint, jsonify
import pandas as pd
import numpy as np

api_bp = Blueprint("api", __name__)


def get_t():
    from render.state import trader
    return trader


def compute_metrics(trades: list, equity_curve: list = None) -> dict:
    if not trades:
        return {}
    df = pd.DataFrame(trades)
    if "pnl" not in df.columns:
        return {}
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0)
    total_pnl = df["pnl"].sum()
    wins = df[df["pnl"] > 0]
    losses = df[df["pnl"] < 0]
    total_trades = len(df)
    win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
    avg_win = wins["pnl"].mean() if len(wins) > 0 else 0
    avg_loss = abs(losses["pnl"].mean()) if len(losses) > 0 else 0
    gross_profit = wins["pnl"].sum() if len(wins) > 0 else 0
    gross_loss = abs(losses["pnl"].sum()) if len(losses) > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
    sharpe = 0
    dd = 0
    if equity_curve and len(equity_curve) > 1:
        eq = pd.Series(equity_curve)
        returns = eq.pct_change().dropna()
        if returns.std() > 0:
            sharpe = returns.mean() / returns.std() * np.sqrt(365 * 24 * 4)
        peak = eq.cummax()
        dd = ((eq - peak) / peak * 100).min()
    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(total_pnl, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "profit_factor": round(profit_factor, 2),
        "sharpe": round(sharpe, 2),
        "max_drawdown_pct": round(dd, 2),
    }


@api_bp.route("/api/status")
def api_status():
    t = get_t()
    if not t:
        return jsonify({"error": "Trader not initialized"})
    from render.state import trader_lock
    with trader_lock:
        trades = t.trades
        trades_serializable = t._make_serializable(trades[-50:]) if trades else []
        positions = t._make_serializable(t.positions)
        equity_curve = t.equity_curve
        metrics = compute_metrics(trades, equity_curve) if trades else {}
        state = {
            "symbol": t.symbol,
            "entry_mode": t.entry_mode,
            "exchange_id": t.exchange_id,
            "equity": t.risk_manager.capital,
            "initial_capital": t.initial_capital,
            "positions": positions,
            "trades": trades_serializable,
            "trades_count": len(trades),
            "pending_orders": len(t.pending_orders),
            "pending_ltf": len(t.pending_ltf_orders),
            "last_4h_ts": str(t.last_4h_ts) if t.last_4h_ts else None,
            "metrics": metrics,
            "equity_curve": equity_curve if len(equity_curve) > 1 else None,
            "updated_at": str(pd.Timestamp.now()),
        }
        return jsonify(state)


@api_bp.route("/api/trades")
def api_trades():
    t = get_t()
    if not t:
        return jsonify([])
    from render.state import trader_lock
    with trader_lock:
        trades = t._make_serializable(t.trades)
        return jsonify(trades)


@api_bp.route("/api/metrics")
def api_metrics():
    t = get_t()
    if not t:
        return jsonify({})
    from render.state import trader_lock
    with trader_lock:
        trades = t.trades
        metrics = compute_metrics(trades, t.equity_curve) if trades else {}
        return jsonify(metrics)
