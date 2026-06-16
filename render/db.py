import os, json, logging
from datetime import datetime
from typing import Optional
import psycopg2
import psycopg2.extras
import numpy as np

log = logging.getLogger(__name__)

DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    raise RuntimeError("DATABASE_URL environment variable required")


def get_conn():
    return psycopg2.connect(DB_URL, sslmode="require")


def init_db():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS trader_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    signal_time TEXT,
                    entry_time TEXT,
                    exit_time TEXT,
                    direction TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    stop_loss REAL,
                    position_size REAL,
                    pnl REAL,
                    exit_reason TEXT,
                    phase TEXT,
                    range_id INTEGER,
                    partial_exited BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    signal_time TEXT,
                    entry_time TEXT,
                    direction TEXT,
                    entry_price REAL,
                    position_size REAL,
                    stop_loss REAL,
                    original_sl REAL,
                    original_risk REAL,
                    phase TEXT,
                    range_id INTEGER,
                    inv_price REAL,
                    stop_price REAL,
                    partial_exited BOOLEAN DEFAULT FALSE,
                    status TEXT DEFAULT 'open',
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
        conn.commit()
        log.info("Database initialized")
    finally:
        conn.close()


def save_state(equity: float, last_4h_ts: Optional[str], last_15m_ts: Optional[str],
               positions: list, processed_indices: list, pending_orders: list,
               pending_ltf: list, pending_signals: list):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            data = {
                "equity": equity,
                "last_4h_ts": last_4h_ts,
                "last_15m_ts": last_15m_ts,
                "positions": positions,
                "processed_indices": [str(i) for i in processed_indices],
                "pending_orders": pending_orders,
                "pending_ltf": pending_ltf,
                "pending_signals": pending_signals,
            }
            cur.execute(
                "INSERT INTO trader_state (key, value, updated_at) VALUES (%s, %s, NOW()) "
                "ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()",
                ("trader_state", json.dumps(data), json.dumps(data))
            )
            cur.execute(
                "INSERT INTO trader_state (key, value, updated_at) VALUES (%s, %s, NOW()) "
                "ON CONFLICT (key) DO UPDATE SET value = %s, updated_at = NOW()",
                ("equity", str(equity), str(equity))
            )
        conn.commit()
    finally:
        conn.close()


def load_state() -> Optional[dict]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM trader_state WHERE key = 'trader_state'")
            row = cur.fetchone()
            if row:
                return json.loads(row[0])
        return None
    finally:
        conn.close()


def save_trade(trade: dict):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO trades (symbol, signal_time, entry_time, exit_time, direction, "
                "entry_price, exit_price, stop_loss, position_size, pnl, exit_reason, "
                "phase, range_id, partial_exited) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (trade.get("symbol"), str(trade.get("signal_time", "")),
                 str(trade.get("entry_time", "")), str(trade.get("exit_time", "")),
                 trade.get("direction"), float(trade.get("entry_price", 0)),
                 float(trade.get("exit_price", 0)), float(trade.get("stop_loss", 0)),
                 float(trade.get("position_size", 0)), float(trade.get("pnl", 0)),
                 trade.get("exit_reason"), trade.get("phase"),
                 int(trade.get("range_id", 0)), bool(trade.get("partial_exited", False)))
            )
        conn.commit()
    finally:
        conn.close()


def load_trades() -> list:
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM trades ORDER BY created_at DESC")
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    finally:
        conn.close()


def clear_positions():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM positions")
        conn.commit()
    finally:
        conn.close()


def save_positions(positions: list):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            for p in positions:
                cur.execute(
                    "INSERT INTO positions (symbol, signal_time, entry_time, direction, "
                    "entry_price, position_size, stop_loss, original_sl, original_risk, "
                    "phase, range_id, inv_price, stop_price, partial_exited, status) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (p.get("symbol"), str(p.get("signal_time", "")),
                     str(p.get("entry_time", "")), p.get("direction"),
                     float(p.get("entry_price", 0)), float(p.get("position_size", 0)),
                     float(p.get("stop_loss", 0)), float(p.get("original_sl", 0)),
                     float(p.get("original_risk", 0)), p.get("phase"),
                     int(p.get("range_id", 0)),
                     float(p.get("inv_price", 0)) if p.get("inv_price") else None,
                     float(p.get("stop_price", 0)) if p.get("stop_price") else None,
                     bool(p.get("partial_exited", False)), "open")
                )
        conn.commit()
    finally:
        conn.close()
