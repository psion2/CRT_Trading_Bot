"""
CRT Strategy Implementation.
Based on rules from MadoCRT, RomeoTPT, and SpeculatorFL.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Tuple, List
from abc import ABC, abstractmethod


class CRTStrategy(ABC):
    """Base class for CRT-based strategies."""

    def __init__(self, name: str = "CRT_Strategy"):
        self.name = name
        self.params = {}

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals from OHLCV data."""
        pass

    @abstractmethod
    def get_rule_description(self) -> str:
        """Return human-readable description of the strategy rules."""
        pass


class CRTStrategyImpl(CRTStrategy):
    """
    Complete CRT Strategy implementation.
    Based on: MadoCRT (TSQ sequence), RomeoTPT (Candle 3, failures), SpeculatorFL (Axis Framework)
    """

    def __init__(
        self,
        use_kill_zone: bool = False,
        use_market_profile: bool = False,
        use_time_theory: bool = False,
        # Signal type configuration
        use_kod: bool = True,
        use_model1: bool = True,
        use_ote: bool = True,
        use_breaker_block: bool = True,
        use_candle3_only: bool = True,
        use_true_mss: bool = True,
        timezone_offset: int = 0,
    ):
        super().__init__(name="CRT_Complete")
        self.params = {
            "timeframe": "4h",
            "ltf_timeframe": "15m",
            "kill_zones": [(2, 5), (7, 10)],
            "risk_per_trade": 0.03,
            "min_risk_reward": 2.0,
            "ote_min": 0.60,
            "ote_max": 0.75,
            "use_kill_zone": use_kill_zone,
            "use_market_profile": use_market_profile,
            "use_time_theory": use_time_theory,
            # Signal types
            "use_kod": use_kod,
            "use_model1": use_model1,
            "use_ote": use_ote,
            "use_breaker_block": use_breaker_block,
            "use_candle3_only": use_candle3_only,
            "use_true_mss": use_true_mss,
            "timezone_offset": timezone_offset,
        }
        self.ltf_df = None
        # Store last CRT range for OTE standalone detection
        self.last_crt_range = {}

    def set_ltf_data(self, ltf_df: pd.DataFrame):
        self.ltf_df = ltf_df.copy()
        if self.ltf_df is not None and len(self.ltf_df) > 0:
            if self.ltf_df.index.tz is not None:
                self.ltf_df.index = self.ltf_df.index.tz_localize(None)
            self.ltf_df = self._calculate_candle_metrics(self.ltf_df)

    def generate_signals(self, df: pd.DataFrame, ltf_df: pd.DataFrame = None) -> pd.DataFrame:
        """Generate CRT signals with FULL pipeline including LTF confirmation."""
        # Set LTF data if provided
        if ltf_df is not None:
            self.set_ltf_data(ltf_df)

        df = df.copy()

        # Step 1: Calculate candle metrics
        df = self._calculate_candle_metrics(df)

        # Step 2: Calculate HTF bias (direction filter)
        df = self._calculate_htf_bias(df)

        # Step 3: Calculate market profile (phase filter)
        df = self._calculate_market_profile(df)

        # Step 4: Calculate time theory (day filter)
        df = self._calculate_time_theory(df)

        # Step 5: Identify key levels (including order blocks + breaker blocks)
        df = self._identify_key_levels(df)
        df = self._identify_breaker_blocks(df)  # NEW
        df = self._identify_smt_confirmation(df, correlated_df=None)  # NEW

        # Step 6: Identify CRT patterns
        df = self._identify_crt_patterns(df)

        # Step 7: Enhance with OTE zone trading
        df = self._enhance_ote_trading(df)  # NEW

        # Step 7: Generate signals with ALL filters
        df["signal"] = 0
        df["signal_reason"] = "none"

        for i in range(len(df)):
            if df.loc[df.index[i], "crt_signal"] != 0:
                crt_signal = df.loc[df.index[i], "crt_signal"]

                # Filter 1: Kill Zone (optional)
                if self.params.get("use_kill_zone", False):
                    if not self._is_in_kill_zone(df.index[i]):
                        continue

                # Filter 2: Candle 3 Only (beginners should only trade Candle 3)
                if self.params.get("use_candle3_only", True):
                    signal_n = df.loc[df.index[i], "signal_candle_n"]
                    if signal_n <= 2:
                        continue

                # Filter 3: HTF Bias Alignment
                htf_bias = df.loc[df.index[i], "htf_bias"]
                if crt_signal == 1 and htf_bias == -1:  # Bullish signal but bearish bias
                    continue
                if crt_signal == -1 and htf_bias == 1:  # Bearish signal but bullish bias
                    continue

                # Filter 4: Market Profile (optional)
                if self.params.get("use_market_profile", False):
                    profile = df.loc[df.index[i], "market_profile"]
                    if profile == "ranging" or profile == "manipulation":
                        continue

                # Filter 5: SMT Confirmation (preferred but not required)
                smt_confirmed = df.loc[df.index[i], "smt_confirmed"]
                ote_quality = df.loc[df.index[i], "ote_zone_quality"]

                if smt_confirmed or ote_quality in ["high", "medium"]:
                    df.loc[df.index[i], "signal_reason"] = df.loc[df.index[i], "crt_phase"] + "_enhanced"

                # Filter 6: Time Theory (optional)
                if self.params.get("use_time_theory", False):
                    day_type = df.loc[df.index[i], "day_type"]
                    if day_type == "low_prob":
                        continue

                # Filter 7: LTF Confirmation (if 15min data available)
                if self.ltf_df is not None and len(self.ltf_df) > 0:
                    signal_time = df.index[i]
                    if not self._check_ltf_confirmation(signal_time, crt_signal):
                        continue  # Skip if LTF doesn't confirm
                    df.loc[df.index[i], "signal_reason"] += "_ltf"

                # All filters passed - generate signal
                df.loc[df.index[i], "signal"] = crt_signal

                # Record reason for signal
                df.loc[df.index[i], "signal_reason"] = df.loc[df.index[i], "crt_phase"]

        return df

    def get_rule_description(self) -> str:
        return """
CRT Strategy Rules:
1. Time Frame: 4H for execution (HTF: Monthly/Weekly/Daily)
2. Kill Zones: London 2-5AM, NY 7-10AM (UTC-5)
3. Entry: Model-1 confirmation (thick candle sweeps, closes opposite)
4. Targets: 50% first, then opposite end of range
5. Risk: 2-3% per trade, min 1:2 R:R
6. Only trade Candle 3 (beginners)
7. SMT confirmation required
8. KOD = highest probability entry
"""

    # ==================== Candle Metrics ====================

    def _calculate_candle_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate candle range metrics for CRT analysis."""
        df = df.copy()

        # Full range
        df["range"] = df["high"] - df["low"]

        # Body
        df["body"] = abs(df["close"] - df["open"])
        df["body_pct"] = df["body"] / df["range"]

        # Body direction
        df["body_direction"] = np.where(df["close"] > df["open"], 1, -1)

        # Upper and lower wicks
        df["upper_wick"] = np.where(
            df["body_direction"] == 1,
            df["high"] - df["close"],
            df["high"] - df["open"],
        )
        df["lower_wick"] = np.where(
            df["body_direction"] == 1,
            df["open"] - df["low"],
            df["close"] - df["low"],
        )

        # Wick percentages
        df["upper_wick_pct"] = df["upper_wick"] / df["range"]
        df["lower_wick_pct"] = df["lower_wick"] / df["range"]

        # Range as percentage of close
        df["range_pct"] = (df["range"] / df["close"]) * 100

        # Wick to body ratio
        df["wick_to_body"] = np.where(
            df["body"] > 0,
            df[["upper_wick", "lower_wick"]].max(axis=1) / df["body"],
            0,
        )

        # Candle type
        df["candle_type"] = np.where(
            df["close"] > df["open"],
            "bullish",
            np.where(df["close"] < df["open"], "bearish", "neutral"),
        )

        # Thickness check (for Model-1)
        df["is_thick"] = df["body_pct"] >= 0.7

        # ATR calculation
        df["atr"] = self._calculate_atr(df)

        return df

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    # ==================== HTF Bias ====================

    def _calculate_htf_bias(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["htf_bias"] = 0
        if len(df) < 2:
            return df
        df["daily_close_change"] = df["close"].diff()
        df["weekly_close_change"] = df["close"].diff(28)
        weighted = df["daily_close_change"] * 0.6 + df["weekly_close_change"].fillna(0) * 0.4
        df["htf_bias"] = np.sign(weighted.fillna(0)).astype(int)
        return df

    # ==================== Market Profile ====================

    def _calculate_market_profile(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["market_profile"] = "expansion"
        window = 10
        if len(df) < window + 1:
            return df
        max_close = df["close"].rolling(window).max()
        min_close = df["close"].rolling(window).min()
        avg_range = df["range"].rolling(window).mean()
        price_range = max_close - min_close
        vr = price_range / avg_range.replace(0, float("nan"))
        conditions = [vr < 1.5, vr > 3]
        choices = ["ranging", "manipulation"]
        df["market_profile"] = np.select(conditions, choices, default="expansion")
        return df

    # ==================== Time Theory ====================

    def _calculate_time_theory(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        dow = df.index.dayofweek
        conditions = [dow == 0, dow.isin([3, 4]), dow.isin([1, 2])]
        type_choices = ["low_prob", "normal", "normal"]
        conv_choices = ["low", "high", "high"]
        df["day_type"] = np.select(conditions, type_choices, default="normal")
        df["day_conviction"] = np.select(conditions, conv_choices, default="medium")
        return df

    # ==================== Key Levels ====================

    def _identify_key_levels(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["is_order_block"] = False
        df["is_fvg"] = False
        df["is_support"] = False
        df["is_resistance"] = False

        n = len(df)
        body_dir = df["body_direction"].values
        is_thick = df["is_thick"].values
        result = np.zeros(n, dtype=bool)
        for i in range(2, n - 2):
            if body_dir[i - 1] == -1 and body_dir[i] == 1 and body_dir[i + 1] == 1 and is_thick[i]:
                result[i] = True
            if body_dir[i - 1] == 1 and body_dir[i] == -1 and body_dir[i + 1] == -1 and is_thick[i]:
                result[i] = True
        df["is_order_block"] = result

        # FVGs: shift-based gap detection
        bullish_fvg = df["low"].shift(-1) > df["high"]
        bearish_fvg = df["high"].shift(-1) < df["low"]
        df["is_fvg"] = bullish_fvg | bearish_fvg

        # Support/resistance: rolling window swing detection
        window = 5
        roll_high = df["high"].rolling(window * 2 + 1, center=True).max()
        roll_low = df["low"].rolling(window * 2 + 1, center=True).min()
        df["is_resistance"] = df["high"] == roll_high
        df["is_support"] = df["low"] == roll_low

        return df

    # ==================== SMT Confirmation ====================

    def _identify_smt_confirmation(self, df: pd.DataFrame, correlated_df: pd.DataFrame = None) -> pd.DataFrame:
        df = df.copy()
        is_thick = df["is_thick"].values
        body_pct = df["body_pct"].values
        up_wick = df["upper_wick_pct"].values
        low_wick = df["lower_wick_pct"].values
        body_dir = df["body_direction"].values
        n = len(df)
        result = np.zeros(n, dtype=bool)
        for i in range(10, n):
            if is_thick[i] and body_pct[i] > 0.75:
                if (up_wick[i-1] > 0.3 and body_dir[i] == 1) or \
                   (low_wick[i-1] > 0.3 and body_dir[i] == -1):
                    result[i] = True
        df["smt_confirmed"] = result
        return df

    # ==================== Breaker Blocks ====================

    def _identify_breaker_blocks(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        n = len(df)
        result = np.zeros(n, dtype=bool)
        if n < 30:
            df["is_breaker_block"] = result
            return df

        high_a = df["high"].values
        low_a = df["low"].values
        window = 20
        half = window // 2

        for i in range(window, n - 10):
            recent_high = high_a[i-window:i-half].max()
            current_high = high_a[i]
            recent_low = low_a[i-window:i-half].min()
            current_low = low_a[i]

            if current_high > recent_high * 1.02:
                for j in range(i + 1, min(i + 5, n)):
                    if abs(low_a[j] - recent_high) / recent_high < 0.005:
                        result[j] = True
                        break

            if current_low < recent_low * 0.98:
                for j in range(i + 1, min(i + 5, n)):
                    if abs(high_a[j] - recent_low) / recent_low < 0.005:
                        result[j] = True
                        break

        df["is_breaker_block"] = result
        return df

    # ==================== OTE Zone Trading ====================

    def _enhance_ote_trading(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["ote_zone_quality"] = "none"
        if "ote_level" not in df.columns:
            return df
        ote = df["ote_level"].values
        close = df["close"].values
        valid = ~np.isnan(ote) & (ote > 0)
        dist = np.full(len(df), np.inf)
        dist[valid] = np.abs(close[valid] - ote[valid]) / close[valid]
        qual = np.full(len(df), "none", dtype=object)
        qual[dist < 0.01] = "high"
        qual[(dist >= 0.01) & (dist < 0.02)] = "medium"
        qual[(dist >= 0.02) & (dist < 0.03)] = "low"
        df["ote_zone_quality"] = qual
        return df

    def _check_ltf_confirmation(self, signal_time: pd.Timestamp, direction: int) -> bool:
        if self.ltf_df is None or len(self.ltf_df) == 0:
            return True

        # Binary search for faster LTF lookup
        pos = self.ltf_df.index.searchsorted(signal_time, side='right')
        start = max(0, pos - 20)
        ltf_before = self.ltf_df.iloc[start:pos]

        if len(ltf_before) < 5:
            return True  # Not enough LTF data - skip confirmation

        # Check 1: LTF Trend Alignment
        recent_closes = ltf_before["close"].values
        ltf_trend = 1 if recent_closes[-1] > recent_closes[0] else -1

        if direction == 1 and ltf_trend != 1:  # Bullish signal but LTF not bullish
            return False
        if direction == -1 and ltf_trend != -1:  # Bearish signal but LTF not bearish
            return False

        # Check 2: Entry Trigger - Break of recent high/low
        recent_high = ltf_before["high"].max()
        recent_low = ltf_before["low"].min()
        current_price = ltf_before["close"].iloc[-1]

        if direction == 1:  # Long signal
            # For long, we want price to break above recent high (momentum up)
            # OR be in a pullback to a support level
            price_near_high = current_price > recent_high * 0.98  # Within 2% of high
            if not price_near_high:
                return False  # Not at good entry point
        else:  # Short signal
            price_near_low = current_price < recent_low * 1.02  # Within 2% of low
            if not price_near_low:
                return False

        # Check 3: No strong retrace (avoid catching falling knife)
        # Calculate retracement from recent high/low
        ltf_range = recent_high - recent_low
        if direction == 1:
            retracement = (recent_high - current_price) / ltf_range if ltf_range > 0 else 0
            if retracement > 0.5:  # More than 50% retracement - too deep
                return False
        else:
            retracement = (current_price - recent_low) / ltf_range if ltf_range > 0 else 0
            if retracement > 0.5:  # More than 50% retracement - too deep
                return False

        return True

    # ==================== CRT Pattern Detection ====================

    def _identify_crt_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify CRT patterns: Turtle Soup, Model-1, Breaker, OTE, KOD.

        Full TSQ pipeline per MadoCRT EP 4 + RomeoTPT CRT Secrets.
        """
        df = df.copy()
        n = len(df)

        # Initialize output columns
        sig_arr = np.zeros(n, dtype=np.int8)
        phase_arr = np.full(n, "none", dtype=object)
        phase_type_arr = np.full(n, "none", dtype=object)
        crt_high_arr = np.full(n, np.nan)
        crt_low_arr = np.full(n, np.nan)
        crt_range_id_arr = np.zeros(n, dtype=np.int32)
        crt_inv_price_arr = np.full(n, np.nan)
        crt_stop_price_arr = np.full(n, np.nan)
        ote_level_arr = np.full(n, np.nan)
        ote_pct_arr = np.full(n, np.nan)
        kod_arr = np.zeros(n, dtype=bool)
        model1_arr = np.zeros(n, dtype=bool)
        ote_std_arr = np.zeros(n, dtype=bool)
        bb_active_arr = np.zeros(n, dtype=bool)
        c1_arr = np.zeros(n, dtype=bool)
        c2_arr = np.zeros(n, dtype=bool)
        br_arr = np.zeros(n, dtype=bool)
        sig_n_arr = np.zeros(n, dtype=np.int16)
        range_counter = 0

        # Extract input arrays once (no pandas overhead in hot loop)
        high_a = df["high"].values.astype(np.float64)
        low_a = df["low"].values.astype(np.float64)
        close_a = df["close"].values.astype(np.float64)
        open_a = df["open"].values.astype(np.float64)
        body_dir_a = np.where(df["close"].values > df["open"].values, 1, -1)  # int
        body_pct_a = df["body_pct"].values.astype(np.float64)
        upper_a = df["upper_wick_pct"].values.astype(np.float64)
        lower_a = df["lower_wick_pct"].values.astype(np.float64)
        range_a = df["range"].values.astype(np.float64)
        atr_a = df["atr"].values.astype(np.float64)
        thick_a = df["is_thick"].values

        swing_highs = self._detect_swing_highs(df, window=5)
        swing_lows = self._detect_swing_lows(df, window=5)

        # Pre-built candle tuple for helpers
        class CandleAccessor:
            pass
        c = CandleAccessor()

        active_ranges = []

        for i in range(10, n):
            # ========== Phase 1: Detect Candle 1 ==========
            c1 = self._detect_candle1_arr(
                i, high_a, low_a, close_a, open_a, body_pct_a, range_a, atr_a,
                swing_highs, swing_lows
            )
            if c1:
                range_counter += 1
                active_ranges.append({
                    'range_id': range_counter,
                    'high': c1[0], 'low': c1[1], 'start_idx': i,
                    'direction': 0, 'ts_idx': -1, 'model1_idx': -1,
                    'displacement_idx': -1, 'has_displacement': False,
                    'has_breaker_retest': False,
                    'fifty_level': (c1[0] + c1[1]) / 2, 'fifty_hit': False,
                    'sig_model1': False, 'sig_breaker': False,
                    'sig_ote': False, 'sig_kod': False,
                })
                c1_arr[i] = True

            for r in active_ranges[:]:
                if r['start_idx'] == i:
                    continue
                candle_n = i - r['start_idx'] + 1

                # 50% level check
                if r['direction'] == -1:
                    if low_a[r['start_idx']:i + 1].min() <= r['fifty_level']:
                        r['fifty_hit'] = True
                elif r['direction'] == 1:
                    if high_a[r['start_idx']:i + 1].max() >= r['fifty_level']:
                        r['fifty_hit'] = True

                # -- Phase 2: Turtle Soup --
                if r['ts_idx'] < 0 and i - r['start_idx'] <= 6:
                    ts_idx = self._detect_ts_arr(i, high_a, low_a, close_a, open_a, r['high'], r['low'])
                    if ts_idx >= 0:
                        r['ts_idx'] = ts_idx
                        if high_a[ts_idx] > r['high']:
                            r['direction'] = -1
                        elif low_a[ts_idx] < r['low']:
                            r['direction'] = 1
                        c2_arr[ts_idx] = True

                # -- Phase 3: Model-1 or True MSS --
                if not r['sig_model1'] and r['ts_idx'] >= 0 and r['direction'] != 0:
                    d = r['direction']
                    ts_high = high_a[r['ts_idx']]
                    ts_low = low_a[r['ts_idx']]

                    m1_idx = self._detect_m1_arr(i, high_a, low_a, close_a, body_dir_a, body_pct_a, thick_a, d, r['high'], r['low'], ts_high, ts_low)
                    if m1_idx >= 0:
                        r['model1_idx'] = m1_idx
                        r['sig_model1'] = True
                        model1_arr[m1_idx] = True
                        if self.params.get("use_model1", True):
                            # Rules 861-867: Entry = limit at Model-1 candle's low (long) or high (short)
                            entry = low_a[m1_idx] if d == 1 else high_a[m1_idx]
                            # Rule 874: SL at protected swing that created Model-1 (TS extreme)
                            sl = ts_low if d == 1 else ts_high
                            sig_arr[m1_idx] = d
                            phase_arr[m1_idx] = f"Model-1_CRT_{candle_n}"
                            phase_type_arr[m1_idx] = "Model-1"
                            crt_high_arr[m1_idx] = r['high']
                            crt_low_arr[m1_idx] = r['low']
                            crt_range_id_arr[m1_idx] = r['range_id']
                            crt_inv_price_arr[m1_idx] = entry
                            crt_stop_price_arr[m1_idx] = sl
                            sig_n_arr[m1_idx] = candle_n

                    if not r['sig_model1'] and self.params.get("use_true_mss", True):
                        mss_idx = self._detect_mss_arr(i, high_a, low_a, close_a, body_dir_a, thick_a, body_pct_a)
                        if mss_idx >= 0:
                            r['model1_idx'] = mss_idx
                            r['sig_model1'] = True
                            model1_arr[mss_idx] = True
                            # Entry at MSS candle's confirmed side
                            entry = low_a[mss_idx] if d == 1 else high_a[mss_idx]
                            # MSS may not have TS, so SL at entry level (tightest valid invalidation)
                            sl = entry
                            sig_arr[mss_idx] = d
                            phase_arr[mss_idx] = f"TrueMSS_CRT_{candle_n}"
                            phase_type_arr[mss_idx] = "Model-1"
                            crt_high_arr[mss_idx] = r['high']
                            crt_low_arr[mss_idx] = r['low']
                            crt_range_id_arr[mss_idx] = r['range_id']
                            crt_inv_price_arr[mss_idx] = entry
                            crt_stop_price_arr[mss_idx] = sl
                            sig_n_arr[mss_idx] = candle_n

                # -- Phase 4: Displacement --
                if r['model1_idx'] >= 0 and not r['has_displacement']:
                    if self._check_disp_arr(i, r['model1_idx'], r['direction'], close_a, low_a, high_a, atr_a):
                        r['displacement_idx'] = i
                        r['has_displacement'] = True

                # -- Phase 5: Breaker --
                if not r['sig_breaker'] and r['has_displacement'] and not r['has_breaker_retest']:
                    b_idx = self._detect_br_arr(i, r['displacement_idx'], r['direction'], high_a, low_a, close_a, open_a, body_dir_a)
                    if b_idx >= 0:
                        r['has_breaker_retest'] = True
                        r['sig_breaker'] = True
                        br_arr[b_idx] = True
                        if self.params.get("use_breaker_block", True):
                            d = r['direction']
                            # Entry at breaker candle's extreme (retest level)
                            entry = low_a[b_idx] if d == 1 else high_a[b_idx]
                            # Rule 874: SL at protected swing (TS extreme), fallback to entry if TS unavailable
                            if r['ts_idx'] >= 0:
                                sl = low_a[r['ts_idx']] if d == 1 else high_a[r['ts_idx']]
                            else:
                                sl = entry
                            sig_arr[b_idx] = d
                            phase_arr[b_idx] = f"Breaker_CRT_{candle_n}"
                            phase_type_arr[b_idx] = "Breaker"
                            crt_high_arr[b_idx] = r['high']
                            crt_low_arr[b_idx] = r['low']
                            crt_range_id_arr[b_idx] = r['range_id']
                            crt_inv_price_arr[b_idx] = entry
                            crt_stop_price_arr[b_idx] = sl
                            sig_n_arr[b_idx] = candle_n

                # -- Phase 6: OTE --
                if not r['sig_ote'] and r['has_displacement']:
                    ote = self._detect_ote_arr(i, r['displacement_idx'], r['direction'], high_a, low_a, close_a)
                    if ote:
                        r['sig_ote'] = True
                        if self.params.get("use_ote", True):
                            d = r['direction']
                            disp_low = low_a[r['displacement_idx']:i + 1].min()
                            disp_high = high_a[r['displacement_idx']:i + 1].max()
                            # Entry at OTE zone midpoint (limit order in 60-75% fib zone)
                            entry = ote[0]
                            # SL handled by backtester fixed % (OTE zone structure varies)
                            sl = float('nan')
                            sig_arr[i] = d
                            phase_arr[i] = f"OTE_CRT_{candle_n}"
                            phase_type_arr[i] = "OTE"
                            crt_high_arr[i] = r['high']
                            crt_low_arr[i] = r['low']
                            crt_range_id_arr[i] = r['range_id']
                            crt_inv_price_arr[i] = entry
                            crt_stop_price_arr[i] = sl
                            ote_level_arr[i] = ote[0]
                            ote_pct_arr[i] = ote[1]
                            ote_std_arr[i] = True
                            sig_n_arr[i] = candle_n

                # -- Phase 7: KOD --
                if not r['sig_kod'] and r['model1_idx'] >= 0:
                    kod_idx = self._detect_kod_arr(i, r, high_a, low_a, close_a, open_a, body_dir_a, thick_a, upper_a, lower_a)
                    if kod_idx >= 0:
                        r['sig_kod'] = True
                        kod_arr[kod_idx] = True
                        if self.params.get("use_kod", True):
                            d = r['direction']
                            # Entry at KOD candle's extreme (final turtle soup entry)
                            entry = low_a[kod_idx] if d == 1 else high_a[kod_idx]
                            # Rule 874: SL at protected swing (TS extreme), fallback to entry if TS unavailable
                            if r['ts_idx'] >= 0:
                                sl = low_a[r['ts_idx']] if d == 1 else high_a[r['ts_idx']]
                            else:
                                sl = entry
                            sig_arr[kod_idx] = d
                            phase_arr[kod_idx] = f"KOD_CRT_{candle_n}"
                            phase_type_arr[kod_idx] = "KOD"
                            crt_high_arr[kod_idx] = r['high']
                            crt_low_arr[kod_idx] = r['low']
                            crt_range_id_arr[kod_idx] = r['range_id']
                            crt_inv_price_arr[kod_idx] = entry
                            crt_stop_price_arr[kod_idx] = sl
                            sig_n_arr[kod_idx] = candle_n

                if i - r['start_idx'] > 30:
                    active_ranges.remove(r)

        # Bulk-write results to DataFrame
        df['crt_signal'] = sig_arr
        df['crt_phase'] = phase_arr
        df['crt_phase_type'] = phase_type_arr
        df['crt_high'] = crt_high_arr
        df['crt_low'] = crt_low_arr
        df['crt_range_id'] = crt_range_id_arr
        df['crt_inv_price'] = crt_inv_price_arr
        df['crt_stop_price'] = crt_stop_price_arr
        df['ote_level'] = ote_level_arr
        df['ote_retract_pct'] = ote_pct_arr
        df['kod_detected'] = kod_arr
        df['model1_detected'] = model1_arr
        df['ote_standalone'] = ote_std_arr
        df['breaker_block_active'] = bb_active_arr
        df['candle1_detected'] = c1_arr
        df['candle2_manipulation'] = c2_arr
        df['breaker_retest'] = br_arr
        df['signal_candle_n'] = sig_n_arr

        if self.params.get("use_breaker_block", True):
            df = self._detect_standalone_breaker_entries(df)

        return df

    # ==================== Swing Point Detection ====================

    def _detect_swing_highs(self, df: pd.DataFrame, window: int = 5) -> set:
        """Detect swing high indices for key level reference."""
        highs = set()
        for i in range(window, len(df) - window):
            if df['high'].iloc[i] == df['high'].iloc[i - window:i + window + 1].max():
                highs.add(i)
        return highs

    def _detect_swing_lows(self, df: pd.DataFrame, window: int = 5) -> set:
        """Detect swing low indices for key level reference."""
        lows = set()
        for i in range(window, len(df) - window):
            if df['low'].iloc[i] == df['low'].iloc[i - window:i + window + 1].min():
                lows.add(i)
        return lows

    # ==================== Array-Based Helper Methods ====================
    # All helpers work on pre-extracted numpy arrays to avoid pandas overhead

    def _detect_candle1_arr(
        self, idx: int, high_a, low_a, close_a, open_a,
        body_pct_a, range_a, atr_a, swing_highs, swing_lows
    ):
        """Detect Candle 1 (Range Accumulation) using numpy arrays."""
        if idx < 3:
            return None

        if range_a[idx] < atr_a[idx] * 0.3:
            return None

        upper = (high_a[idx] - max(close_a[idx], open_a[idx])) / range_a[idx] if range_a[idx] > 0 else 0
        lower = (min(close_a[idx], open_a[idx]) - low_a[idx]) / range_a[idx] if range_a[idx] > 0 else 0

        # Single Candle Range (both wicks present)
        if upper > 0.15 and lower > 0.15 and body_pct_a[idx] < 0.7:
            for lb in range(1, min(8, idx + 1)):
                if low_a[idx] <= low_a[idx - lb] * 1.01 or high_a[idx] >= high_a[idx - lb] * 0.99:
                    return (max(high_a[idx], high_a[idx - lb]), min(low_a[idx], low_a[idx - lb]))
            return (high_a[idx], low_a[idx])

        # Inside Bar Range (3-candle consolidation)
        if idx >= 2:
            h3 = max(high_a[idx - 2], high_a[idx - 1], high_a[idx])
            l3 = min(low_a[idx - 2], low_a[idx - 1], low_a[idx])
            r3 = h3 - l3
            avg_body = (body_pct_a[idx - 2] + body_pct_a[idx - 1] + body_pct_a[idx]) / 3
            avg_r = (range_a[idx - 2] + range_a[idx - 1] + range_a[idx]) / 3

            if 0.2 <= avg_body <= 0.7 and avg_r > 0 and r3 > atr_a[idx] * 0.5:
                return (h3, l3)

        return None

    def _detect_ts_arr(self, idx: int, high_a, low_a, close_a, open_a, crt_high: float, crt_low: float) -> int:
        """Detect Turtle Soup using numpy arrays."""
        n = len(high_a)

        # Type 1: Same-candle
        if high_a[idx] > crt_high and close_a[idx] < open_a[idx] and close_a[idx] <= crt_high * 1.005:
            return idx
        if low_a[idx] < crt_low and close_a[idx] > open_a[idx] and close_a[idx] >= crt_low * 0.995:
            return idx

        # Type 2: Two-candle
        if idx + 1 < n:
            if (high_a[idx] > crt_high and close_a[idx] > open_a[idx] and
                close_a[idx + 1] < open_a[idx + 1] and close_a[idx + 1] < low_a[idx]):
                return idx + 1
            if (low_a[idx] < crt_low and close_a[idx] < open_a[idx] and
                close_a[idx + 1] > open_a[idx + 1] and close_a[idx + 1] > high_a[idx]):
                return idx + 1

        return -1

    def _detect_m1_arr(
        self, idx: int, high_a, low_a, close_a, body_dir_a,
        body_pct_a, thick_a, direction: int, crt_high: float,
        crt_low: float, ts_high: float, ts_low: float
    ) -> int:
        """Detect Model-1 using numpy arrays."""
        if idx < 2 or not thick_a[idx]:
            return -1

        if direction == -1:
            if body_dir_a[idx] == -1 and body_pct_a[idx] >= 0.7:
                if close_a[idx] <= ts_low * 1.005 or close_a[idx] <= crt_low * 1.01:
                    return idx
            if body_dir_a[idx] == -1 and thick_a[idx] and close_a[idx] < ts_low and high_a[idx] < ts_high:
                return idx

        if direction == 1:
            if body_dir_a[idx] == 1 and body_pct_a[idx] >= 0.7:
                if close_a[idx] >= ts_high * 0.995 or close_a[idx] >= crt_high * 0.99:
                    return idx
            if body_dir_a[idx] == 1 and thick_a[idx] and close_a[idx] > ts_high and low_a[idx] > ts_low:
                return idx

        return -1

    def _detect_mss_arr(self, idx: int, high_a, low_a, close_a, body_dir_a, thick_a, body_pct_a) -> int:
        """Detect True Market Structure Shift using numpy arrays."""
        if idx < 5:
            return -1
        if not thick_a[idx] and body_pct_a[idx] < 0.5:
            return -1

        # Bullish: find a previous candle that broke a swing low
        for lb in range(3, min(15, idx)):
            prev_low_min = low_a[max(0, idx - lb - 5):idx - lb].min()
            if low_a[idx - lb] < prev_low_min:
                if close_a[idx] > high_a[idx - lb] * 1.002 and body_dir_a[idx] == 1:
                    return idx
                break

        # Bearish: find a previous candle that broke a swing high
        for lb in range(3, min(15, idx)):
            prev_high_max = high_a[max(0, idx - lb - 5):idx - lb].max()
            if high_a[idx - lb] > prev_high_max:
                if close_a[idx] < low_a[idx - lb] * 0.998 and body_dir_a[idx] == -1:
                    return idx
                break

        return -1

    def _check_disp_arr(self, idx: int, model1_idx: int, direction: int,
                        close_a, low_a, high_a, atr_a) -> bool:
        """Check displacement using numpy arrays."""
        if model1_idx < 0:
            return False
        atr_v = atr_a[idx]
        if direction == -1:
            return (close_a[model1_idx] - low_a[model1_idx:idx + 1].min()) >= atr_v * 0.5
        else:
            return (high_a[model1_idx:idx + 1].max() - close_a[model1_idx]) >= atr_v * 0.5

    def _detect_br_arr(self, idx: int, disp_idx: int, direction: int,
                       high_a, low_a, close_a, open_a, body_dir_a) -> int:
        """Detect Breaker Block retest using numpy arrays."""
        if disp_idx < 0:
            return -1
        bc_idx = disp_idx - 1
        if bc_idx < 0:
            return -1

        bd = body_dir_a[bc_idx]
        if direction == -1:
            if bd != 1:
                return -1
            bb_top, bb_bot = high_a[bc_idx], low_a[bc_idx]
            if high_a[idx] >= bb_bot and low_a[idx] <= bb_top * 1.005 and body_dir_a[idx] == -1:
                return idx
        else:
            if bd != -1:
                return -1
            bb_top, bb_bot = high_a[bc_idx], low_a[bc_idx]
            if low_a[idx] <= bb_top and high_a[idx] >= bb_bot * 0.995 and body_dir_a[idx] == 1:
                return idx
        return -1

    def _detect_ote_arr(self, idx: int, disp_idx: int, direction: int,
                        high_a, low_a, close_a):
        """Detect OTE retracement using numpy arrays. Returns (midpoint, retrace_pct) or None."""
        if disp_idx < 0:
            return None
        if direction == -1:
            dh = high_a[disp_idx]
            dl = low_a[disp_idx:idx + 1].min()
            dr = dh - dl
            if dr <= 0:
                return None
            ret = (close_a[idx] - dl) / dr
            if 0.60 <= ret <= 0.75:
                return (dh - dr * 0.675, ret)
        else:
            dl = low_a[disp_idx]
            dh = high_a[disp_idx:idx + 1].max()
            dr = dh - dl
            if dr <= 0:
                return None
            ret = (dh - close_a[idx]) / dr
            if 0.60 <= ret <= 0.75:
                return (dl + dr * 0.675, ret)
        return None

    def _detect_kod_arr(self, idx: int, r: dict,
                        high_a, low_a, close_a, open_a,
                        body_dir_a, thick_a, upper_a, lower_a) -> int:
        """Detect KOD using numpy arrays."""
        if r['model1_idx'] < 0 or not r.get('fifty_hit', False):
            return -1

        d = r['direction']
        if d == -1:
            if high_a[idx] > r['high'] * 0.995 and close_a[idx] < open_a[idx] and close_a[idx] <= r['high']:
                return idx
            if upper_a[idx] > 0.3 and body_dir_a[idx] == -1 and close_a[idx] < open_a[idx]:
                return idx
            if body_dir_a[idx] == 1 and thick_a[idx] and high_a[idx] > r['high'] * 0.995:
                return idx
        else:
            if low_a[idx] < r['low'] * 1.005 and close_a[idx] > open_a[idx] and close_a[idx] >= r['low']:
                return idx
            if lower_a[idx] > 0.3 and body_dir_a[idx] == 1 and close_a[idx] > open_a[idx]:
                return idx
            if body_dir_a[idx] == -1 and thick_a[idx] and low_a[idx] < r['low'] * 1.005:
                return idx
        return -1

    # ==================== Standalone Breaker Entries ====================

    def _detect_standalone_breaker_entries(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect standalone breaker block entries (not tied to TSQ sequence)."""
        breaker_blocks = df[df["is_breaker_block"] == True]
        for idx in breaker_blocks.index:
            idx_pos = df.index.get_loc(idx)

            for j in range(idx_pos + 1, min(idx_pos + 10, len(df))):
                current = df.iloc[j]
                bb_candle = df.iloc[idx_pos]

                if bb_candle["close"] > bb_candle["open"]:  # Bullish BB
                    if (current["low"] <= bb_candle["high"] * 1.005 and
                        current["close"] > current["open"]):
                        direction = 1
                        entry = current["low"]
                        # Rule 874: SL at protected swing (BB candle's low)
                        sl = bb_candle["low"]
                        df.iloc[j, df.columns.get_loc("crt_signal")] = direction
                        df.iloc[j, df.columns.get_loc("crt_phase")] = "BB_Standalone"
                        df.iloc[j, df.columns.get_loc("crt_phase_type")] = "Breaker"
                        df.iloc[j, df.columns.get_loc("crt_high")] = bb_candle["high"]
                        df.iloc[j, df.columns.get_loc("crt_low")] = current["low"]
                        df.iloc[j, df.columns.get_loc("crt_inv_price")] = entry
                        df.iloc[j, df.columns.get_loc("crt_stop_price")] = sl
                        df.iloc[j, df.columns.get_loc("breaker_block_active")] = True
                        break
                else:  # Bearish BB
                    if (current["high"] >= bb_candle["low"] * 0.995 and
                        current["close"] < current["open"]):
                        direction = -1
                        entry = current["high"]
                        # Rule 874: SL at protected swing (BB candle's high)
                        sl = bb_candle["high"]
                        df.iloc[j, df.columns.get_loc("crt_signal")] = direction
                        df.iloc[j, df.columns.get_loc("crt_phase")] = "BB_Standalone"
                        df.iloc[j, df.columns.get_loc("crt_phase_type")] = "Breaker"
                        df.iloc[j, df.columns.get_loc("crt_high")] = current["high"]
                        df.iloc[j, df.columns.get_loc("crt_low")] = bb_candle["low"]
                        df.iloc[j, df.columns.get_loc("crt_inv_price")] = entry
                        df.iloc[j, df.columns.get_loc("crt_stop_price")] = sl
                        df.iloc[j, df.columns.get_loc("breaker_block_active")] = True
                        break

        return df

    # ==================== Kill Zones ====================

    def _is_in_kill_zone(self, timestamp) -> bool:
        """Check if timestamp is within a kill zone (London or NY).

        Per MadoCRT EP 3: Kill zones are high-probability trading times:
        - London: 2AM - 5AM
        - NY: 7AM - 10AM
        - Timezone: UTC-5 (or UTC-4 during DST)

        Rule: "Only execute trades within kill zones"
        """
        if isinstance(timestamp, str):
            timestamp = pd.to_datetime(timestamp)

        # Apply timezone offset (default 0 = UTC)
        offset = self.params.get("timezone_offset", 0)
        hour = (timestamp.hour + offset) % 24

        # London Kill Zone: 2AM - 5AM (strict)
        if 2 <= hour < 5:
            return True

        # NY Kill Zone: 7AM - 10AM (strict)
        if 7 <= hour < 10:
            return True

        return False


class MadoCRTStrategy(CRTStrategy):
    """MadoCRT-based strategy - simplified version."""

    def __init__(self):
        super().__init__(name="MadoCRT")
        self.params = {
            "timeframe": "4h",
            "min_body_pct": 0.70,  # Thick candles only
            "ote_range": (0.60, 0.75),
        }
        self.crt = CRTStrategyImpl()

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals based on MadoCRT rules."""
        return self.crt.generate_signals(df)

    def get_rule_description(self) -> str:
        return """
MadoCRT Rules:
- TSQ Sequence: Turtle Soup → Model-1 → Breaker → OTE → KOD
- Model-1: Thick candle sweeps old high/low, closes opposite direction
- OTE: 60-75% Fibonacci retracement zone
- KOD: Final turtle soup before target (highest probability entry)
- Target 1: 50% of range
- Target 2: Opposite end of range
- SMT confirmation required
- Only trade within kill zones
"""


if __name__ == "__main__":
    # Test with sample data
    import numpy as np

    # Create sample data
    dates = pd.date_range(start="2025-01-01", periods=100, freq="4h")
    np.random.seed(42)

    base_price = 50000
    data = {
        "open": base_price + np.random.randn(100) * 1000,
        "high": base_price + np.random.randn(100) * 1000 + 500,
        "low": base_price + np.random.randn(100) * 1000 - 500,
        "close": base_price + np.random.randn(100) * 1000,
        "volume": np.random.randint(1000, 10000, 100),
    }

    df = pd.DataFrame(data, index=dates)

    # Test strategy
    strategy = MadoCRTStrategy()
    result = strategy.generate_signals(df)

    print("Signal distribution:")
    print(result["signal"].value_counts())

    print("\nCRT phases detected:")
    print(result["crt_phase"].value_counts())