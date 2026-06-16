"""
One-time migration script: load Colab state from Drive JSON into PostgreSQL.

Usage:
    python migrate_from_colab.py --state /path/to/trader_state.json --trades /path/to/trade_log.csv
"""
import argparse, json, sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from render import db
import pandas as pd


def migrate(state_path: str, trades_path: str = None):
    db.init_db()
    db.clear_positions()

    state = json.load(open(state_path))
    equity = state.get("equity", 10000)
    last_4h = state.get("last_4h_ts")
    last_15m = state.get("last_15m_ts")
    positions = state.get("positions", [])
    processed = state.get("processed_signal_indices", [])
    pending_orders = state.get("pending_orders", [])
    pending_ltf = state.get("pending_ltf_orders", [])
    pending_signals = state.get("pending_signals", [])

    db.save_state(
        equity=equity,
        last_4h_ts=last_4h,
        last_15m_ts=last_15m,
        positions=positions,
        processed_indices=processed,
        pending_orders=pending_orders,
        pending_ltf=pending_ltf,
        pending_signals=pending_signals,
    )

    if positions:
        db.save_positions(positions)
        print(f"Saved {len(positions)} positions")

    if trades_path:
        df = pd.read_csv(trades_path)
        for _, row in df.iterrows():
            trade = {
                "symbol": row.get("symbol", "BTC/USDT"),
                "signal_time": row.get("signal_time", ""),
                "entry_time": row.get("entry_time", ""),
                "exit_time": row.get("exit_time", ""),
                "direction": row.get("direction", ""),
                "entry_price": float(row.get("entry_price", 0)),
                "exit_price": float(row.get("exit_price", 0)),
                "stop_loss": float(row.get("stop_loss", 0)),
                "position_size": float(row.get("position_size", 0)),
                "pnl": float(row.get("pnl", 0)),
                "exit_reason": row.get("exit_reason", ""),
                "phase": row.get("phase", ""),
                "range_id": int(row.get("range_id", 0)),
                "partial_exited": bool(row.get("partial_exited", False)),
            }
            db.save_trade(trade)
        print(f"Migrated {len(df)} trades")

    print(f"State migrated: equity=${equity:,.2f}, positions={len(positions)}, trades={len(df) if trades_path else 'N/A'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate Colab state to PostgreSQL")
    parser.add_argument("--state", required=True, help="Path to trader_state.json")
    parser.add_argument("--trades", help="Path to trade_log.csv")
    args = parser.parse_args()
    migrate(args.state, args.trades)
