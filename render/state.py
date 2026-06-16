import threading

trader = None
trader_lock = threading.Lock()


def set_trader(t):
    global trader
    trader = t
