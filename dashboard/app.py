"""Flask dashboard for CRT Trading Bot - reads paper trader output + backtest results."""

import json
import os
import time
from pathlib import Path

import pandas as pd
import numpy as np
from flask import Flask, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent.parent
PAPER_DIR = BASE_DIR / "paper"
STATE_PATH = PAPER_DIR / "trader_state.json"
TRADE_LOG_PATH = PAPER_DIR / "trade_log.csv"
RESULTS_DIR = Path(__file__).resolve().parent.parent.parent


_last_state: dict = {"error": "Trader not started"}
_last_state_ts: float = 0

def read_state() -> dict:
    """Read the paper trader's state file with caching to avoid IO conflicts."""
    global _last_state, _last_state_ts
    now = time.time()
    if now - _last_state_ts < 1.0:
        return _last_state
    if STATE_PATH.exists():
        try:
            with open(STATE_PATH, "r") as f:
                data = json.load(f)
            _last_state = data
            _last_state_ts = now
            return data
        except (json.JSONDecodeError, OSError):
            return _last_state
    return {"error": "Trader not started"}


def read_trades() -> list:
    """Read trade log CSV and return as list of dicts."""
    if not TRADE_LOG_PATH.exists():
        return []
    try:
        df = pd.read_csv(TRADE_LOG_PATH)
        if df.empty:
            return []
        df["entry_time"] = pd.to_datetime(df["entry_time"], errors="coerce")
        df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")
        df = df.sort_values("exit_time", ascending=False)
        return df.fillna("").to_dict(orient="records")
    except Exception:
        return []


def read_backtest_results() -> list:
    """Read all backtest JSON result files."""
    results = []
    if RESULTS_DIR.exists():
        for f in RESULTS_DIR.glob("*results*.json"):
            try:
                data = json.loads(f.read_text())
                if isinstance(data, list):
                    for r in data:
                        r["_source"] = f.name.replace(".json", "")
                        results.append(r)
            except Exception:
                pass
    return results


def compute_metrics(trades: list, equity_curve: list = None) -> dict:
    """Compute performance metrics from trade list."""
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
    if equity_curve and len(equity_curve) > 1:
        eq = pd.Series(equity_curve)
        returns = eq.pct_change().dropna()
        sharpe = (returns.mean() / returns.std() * np.sqrt(365 * 24 * 4)) if returns.std() > 0 else 0
        peak = eq.cummax()
        dd = ((eq - peak) / peak * 100).min()
    else:
        sharpe = 0
        dd = 0
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


@app.route("/")
def index():
    """Render the main dashboard."""
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    """Return current trader state."""
    state = read_state()
    trades = read_trades()
    state["trades"] = trades[:50]
    state["metrics"] = compute_metrics(trades, state.get("equity_curve"))
    state["trades_count"] = len(trades)
    equity_curve = state.get("equity_curve", [])
    if equity_curve and len(equity_curve) > 1:
        state["equity_curve"] = equity_curve
    else:
        eq = [10000]
        if trades:
            running = 10000
            eq = [running]
            for t in trades:
                running += float(t.get("pnl", 0))
                eq.append(running)
        state["equity_curve"] = eq
    return jsonify(state)


@app.route("/api/trades")
def api_trades():
    """Return all trades."""
    trades = read_trades()
    return jsonify(trades)


@app.route("/api/backtest")
def api_backtest():
    """Return backtest comparison results."""
    results = read_backtest_results()
    return jsonify(results)


@app.route("/api/metrics")
def api_metrics():
    """Return computed metrics."""
    trades = read_trades()
    state = read_state()
    metrics = compute_metrics(trades, state.get("equity_curve"))
    return jsonify(metrics)


def main():
    port = int(os.environ.get("PORT", 5000))
    from waitress import serve
    serve(app, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
