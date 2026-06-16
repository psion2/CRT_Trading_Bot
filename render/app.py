import os, sys, logging
from pathlib import Path

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from paper.paper_trader import PaperTrader
from render import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)
scheduler = BackgroundScheduler(daemon=True)

EXCHANGE_ID = os.environ.get("EXCHANGE_ID", "kucoin")
SYMBOL = os.environ.get("SYMBOL", "BTC/USDT")
ENTRY_MODE = os.environ.get("ENTRY_MODE", "limit_retest")
USE_LTF = os.environ.get("USE_LTF", "false").lower() == "true"
INITIAL_CAPITAL = float(os.environ.get("INITIAL_CAPITAL", "10000"))
RISK_PER_TRADE = float(os.environ.get("RISK_PER_TRADE", "0.02"))
FEE_RATE = float(os.environ.get("FEE_RATE", "0.0004"))
STOP_LOSS_PCT = float(os.environ.get("STOP_LOSS_PCT", "0.02"))
TP1 = float(os.environ.get("TP1", "1.5"))
TP2 = float(os.environ.get("TP2", "2.0"))
ENTRY_LOGIC = os.environ.get("ENTRY_LOGIC", "extreme")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "60"))


def _init_exchange_fallback(trader_obj):
    import ccxt
    fallbacks = [trader_obj.exchange_id, "kucoin", "mexc", "gate", "bybit", "binance"]
    fallbacks = list(dict.fromkeys(fallbacks))
    for exch_id in fallbacks:
        try:
            exchange_class = getattr(ccxt, exch_id, None)
            if exchange_class is None:
                continue
            trader_obj.exchange = exchange_class({"enableRateLimit": True})
            trader_obj.exchange.load_markets()
            trader_obj.exchange_id = exch_id
            log.info(f"Connected to {exch_id}")
            return True
        except Exception as e:
            log.warning(f"Exchange {exch_id} failed: {e}")
    return False


def create_trader():
    from render.state import trader_lock, set_trader
    t = PaperTrader(
        exchange_id=EXCHANGE_ID,
        symbol=SYMBOL,
        entry_mode=ENTRY_MODE,
        use_ltf=USE_LTF,
        initial_capital=INITIAL_CAPITAL,
        risk_per_trade=RISK_PER_TRADE,
        max_leverage=3.0,
        transaction_cost=10.0,
        fee_rate=FEE_RATE,
        stop_loss_pct=STOP_LOSS_PCT,
        tp_ratios=[TP1, TP2],
        entry_logic=ENTRY_LOGIC,
        telegram_token=None,
        telegram_chat_id=None,
        trade_log_path=None,
        state_path=None,
    )
    if not _init_exchange_fallback(t):
        log.error("No exchange available")
        return False

    state = db.load_state()
    if state:
        log.info("Restoring state from database")
        t.trades = db.load_trades()
        t.positions = state.get("positions", [])
        t.risk_manager.capital = state.get("equity", INITIAL_CAPITAL)
        t.equity_curve = [t.risk_manager.capital]
        t.last_4h_ts = state.get("last_4h_ts")
        t.last_15m_ts = state.get("last_15m_ts")
        processed = state.get("processed_indices", [])
        t.processed_signal_indices = set(str(i) for i in processed)
        log.info(f"Restored: {len(t.trades)} trades, {len(t.positions)} positions, ${t.risk_manager.capital:,.2f}")
    else:
        log.info(f"Fresh start: ${INITIAL_CAPITAL:,.0f} capital")

    try:
        t.df_4h = t._fetch_ohlcv("4h", limit=150)
    except Exception as e:
        log.warning(f"Initial 4h fetch failed: {e}")
    try:
        if t.use_ltf:
            t.df_15m = t._fetch_ohlcv("15m", limit=200)
    except Exception as e:
        log.warning(f"Initial 15m fetch failed: {e}")

    t.running = True
    set_trader(t)
    log.info("Trader initialized")
    return True


def get_t():
    from render.state import trader
    return trader


def check_candles():
    t = get_t()
    if not t or not t.running:
        return
    from render.state import trader_lock
    with trader_lock:
        try:
            df_4h_new = t._fetch_ohlcv("4h", limit=150)
            df_15m_new = t._fetch_ohlcv("15m", limit=200) if t.use_ltf else pd.DataFrame()

            has_new_4h = t._is_new_4h_candle(df_4h_new) if not df_4h_new.empty else False
            has_new_15m = t._is_new_15m_candle(df_15m_new) if not df_15m_new.empty else False

            if has_new_4h and not df_4h_new.empty:
                t.df_4h = df_4h_new
                t.last_4h_ts = t.df_4h.index[-1]
                log.info(f"New 4h candle: {t.last_4h_ts}")
                t._update_trailing_stops()
                t._check_positions()
                t._check_retests()
                t._check_limit_orders()
                t._process_4h_candle()

            if has_new_15m and not df_15m_new.empty:
                t.df_15m = df_15m_new
                t.last_15m_ts = t.df_15m.index[-1]
                t._check_ltf_fills()

        except Exception as e:
            log.error(f"Check candles error: {e}", exc_info=True)


def persist_state():
    t = get_t()
    if not t or not t.running:
        return
    from render.state import trader_lock
    with trader_lock:
        try:
            positions_data = t._make_serializable(t.positions)
            pending_orders_data = t._make_serializable(t.pending_orders)
            pending_ltf_data = t._make_serializable(t.pending_ltf_orders)
            pending_signals_data = t._make_serializable(t.pending_signals)
            db.save_state(
                equity=t.risk_manager.capital,
                last_4h_ts=str(t.last_4h_ts) if t.last_4h_ts else None,
                last_15m_ts=str(t.last_15m_ts) if t.last_15m_ts else None,
                positions=positions_data,
                processed_indices=list(t.processed_signal_indices),
                pending_orders=pending_orders_data,
                pending_ltf=pending_ltf_data,
                pending_signals=pending_signals_data,
            )
        except Exception as e:
            log.error(f"Persist state error: {e}")


def create_app():
    db.init_db()

    if not create_trader():
        log.warning("Trader init failed, dashboard will show error state")

    scheduler.add_job(check_candles, "interval", seconds=POLL_INTERVAL, id="check_candles")
    scheduler.add_job(persist_state, "interval", seconds=30, id="persist_state")
    scheduler.start()

    from render.api import api_bp
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        from flask import render_template
        return render_template("index.html")

    @app.route("/api/health")
    def health():
        from flask import jsonify
        t = get_t()
        ok = t is not None and t.running and t.exchange is not None
        return jsonify({"status": "ok" if ok else "error"})

    return app


if __name__ == "__main__":
    import waitress
    port = int(os.environ.get("PORT", 5000))
    app = create_app()
    log.info(f"Starting on port {port}")
    waitress.serve(app, host="0.0.0.0", port=port)
