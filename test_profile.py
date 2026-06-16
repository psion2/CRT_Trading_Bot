"""Profile where the time is spent."""
import time
import sys
sys.path.insert(0, 'E:\\MyWebProject\\CRT_Trading_Bot\\CRT_Trading_Bot')

from data.forex_loader import ForexDataLoader
from strategies.crt_strategy import CRTStrategyImpl

loader = ForexDataLoader()
df = loader.load_forex('EUR_USD')
print(f'Total candles: {len(df)}')

# Use last 100 candles
df_small = df.iloc[-100:].copy()

strat = CRTStrategyImpl()

# Profile each step
import cProfile, pstats
profiler = cProfile.Profile()
profiler.enable()
result = strat.generate_signals(df_small)
profiler.disable()

pstats.Stats(profiler).sort_stats('cumtime').print_stats(20)
print(f'\nSignals: {(result["signal"] != 0).sum()}')
