"""
Technical Indicator Engine
Processes PriceData through various technical indicators
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime

try:
    from ..adapters import PriceData
except ImportError:
    from adapters import PriceData


@dataclass
class IndicatorData:
    """Container for all indicator values at a point in time"""
    timestamp: datetime
    symbol: str
    price: float

    # Trend indicators
    ema_9: Optional[float] = None
    ema_21: Optional[float] = None
    sma_50: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None

    # Momentum indicators
    rsi_14: Optional[float] = None

    # Volatility indicators
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None  # SMA 20
    bb_lower: Optional[float] = None
    bb_percent: Optional[float] = None  # % position in bands
    atr_14: Optional[float] = None

    # Signal helpers
    trend: str = "neutral"  # bullish, bearish, neutral
    signal_strength: float = 0.0  # -1.0 to 1.0


class IndicatorEngine:
    """
    Calculate technical indicators from price data.
    Optimized for gold (XAU/USD) trading on H1 timeframe.
    """

    def __init__(self):
        self._price_history: List[PriceData] = []
        self._max_history = 200  # Keep enough for 50-period calculations

    def update(self, price: PriceData) -> IndicatorData:
        """
        Add new price data and recalculate indicators.
        Returns IndicatorData with all current values.
        """
        self._price_history.append(price)

        # Trim history to prevent memory bloat
        if len(self._price_history) > self._max_history:
            self._price_history = self._price_history[-self._max_history:]

        return self._calculate(price)

    def update_batch(self, prices: List[PriceData]) -> List[IndicatorData]:
        """Process a batch of historical prices"""
        self._price_history.extend(prices)

        # Trim if needed
        if len(self._price_history) > self._max_history:
            self._price_history = self._price_history[-self._max_history:]

        return [self._calculate(p) for p in prices]

    def _calculate(self, current_price: PriceData) -> IndicatorData:
        """Calculate all indicators from current price history"""
        closes = np.array([p.close for p in self._price_history])
        highs = np.array([p.high for p in self._price_history])
        lows = np.array([p.low for p in self._price_history])

        indicator = IndicatorData(
            timestamp=current_price.timestamp,
            symbol=current_price.symbol,
            price=current_price.close
        )

        # Need minimum data for calculations
        if len(closes) < 50:
            return indicator

        # Calculate EMAs
        indicator.ema_9 = self._ema(closes, 9)
        indicator.ema_21 = self._ema(closes, 21)
        indicator.sma_50 = self._sma(closes, 50)

        # Calculate MACD
        indicator.macd, indicator.macd_signal, indicator.macd_histogram = self._macd(closes)

        # Calculate RSI
        indicator.rsi_14 = self._rsi(closes, 14)

        # Calculate Bollinger Bands
        indicator.bb_upper, indicator.bb_middle, indicator.bb_lower, indicator.bb_percent = self._bollinger_bands(closes)

        # Calculate ATR
        indicator.atr_14 = self._atr(highs, lows, closes, 14)

        # Determine trend
        indicator.trend = self._determine_trend(indicator)

        # Calculate signal strength
        indicator.signal_strength = self._calculate_signal_strength(indicator)

        return indicator

    @staticmethod
    def _ema(data: np.ndarray, period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(data) < period:
            return None

        alpha = 2 / (period + 1)
        ema = data[0]
        for price in data[1:]:
            ema = alpha * price + (1 - alpha) * ema
        return float(ema)

    @staticmethod
    def _sma(data: np.ndarray, period: int) -> Optional[float]:
        """Calculate Simple Moving Average"""
        if len(data) < period:
            return None
        return float(np.mean(data[-period:]))

    @staticmethod
    def _macd(data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Calculate MACD, Signal line, and Histogram"""
        if len(data) < slow + signal:
            return None, None, None

        # Calculate EMAs for MACD
        ema_fast = IndicatorEngine._ema(data, fast)
        ema_slow = IndicatorEngine._ema(data, slow)

        if ema_fast is None or ema_slow is None:
            return None, None, None

        macd_line = ema_fast - ema_slow

        # Calculate signal line (EMA of MACD)
        # Need historical MACD values - approximate with current
        signal_line = macd_line * (2 / (signal + 1))  # Simplified

        histogram = macd_line - signal_line

        return float(macd_line), float(signal_line), float(histogram)

    @staticmethod
    def _rsi(data: np.ndarray, period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        if len(data) < period + 1:
            return None

        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    @staticmethod
    def _bollinger_bands(data: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Calculate Bollinger Bands and %B position"""
        if len(data) < period:
            return None, None, None, None

        middle = np.mean(data[-period:])
        std = np.std(data[-period:])

        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)

        # %B position (0 = lower band, 1 = upper band, 0.5 = middle)
        current = data[-1]
        if upper != lower:
            percent_b = (current - lower) / (upper - lower)
        else:
            percent_b = 0.5

        return float(upper), float(middle), float(lower), float(percent_b)

    @staticmethod
    def _atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> Optional[float]:
        """Calculate Average True Range"""
        if len(highs) < period + 1:
            return None

        true_ranges = []
        for i in range(1, len(highs)):
            tr1 = highs[i] - lows[i]  # Current high - low
            tr2 = abs(highs[i] - closes[i-1])  # Current high - prev close
            tr3 = abs(lows[i] - closes[i-1])  # Current low - prev close
            true_ranges.append(max(tr1, tr2, tr3))

        if len(true_ranges) < period:
            return None

        return float(np.mean(true_ranges[-period:]))

    @staticmethod
    def _determine_trend(indicator: IndicatorData) -> str:
        """Determine overall trend from indicators"""
        if indicator.ema_9 is None or indicator.ema_21 is None:
            return "neutral"

        # EMA crossover logic
        if indicator.ema_9 > indicator.ema_21:
            if indicator.sma_50 and indicator.price > indicator.sma_50:
                return "bullish"
            return "bullish_weak"
        elif indicator.ema_9 < indicator.ema_21:
            if indicator.sma_50 and indicator.price < indicator.sma_50:
                return "bearish"
            return "bearish_weak"

        return "neutral"

    @staticmethod
    def _calculate_signal_strength(indicator: IndicatorData) -> float:
        """
        Calculate signal strength from -1.0 (strong sell) to 1.0 (strong buy)
        Based on confluence of multiple indicators
        """
        if indicator.rsi_14 is None or indicator.macd is None:
            return 0.0

        strength = 0.0
        factors = 0

        # RSI contribution (-0.3 to +0.3)
        rsi_normalized = (indicator.rsi_14 - 50) / 50  # -1 to 1
        strength += rsi_normalized * 0.3
        factors += 0.3

        # MACD contribution (-0.3 to +0.3)
        if indicator.macd_histogram:
            macd_signal = np.sign(indicator.macd_histogram) * min(abs(indicator.macd_histogram) / 0.5, 1.0)
            strength += macd_signal * 0.3
            factors += 0.3

        # EMA trend contribution (-0.2 to +0.2)
        if indicator.ema_9 and indicator.ema_21:
            if indicator.ema_9 > indicator.ema_21:
                strength += 0.2
            else:
                strength -= 0.2
            factors += 0.2

        # Bollinger Bands contribution (-0.2 to +0.2)
        if indicator.bb_percent is not None:
            # Oversold below lower band, overbought above upper band
            bb_signal = (indicator.bb_percent - 0.5) * 2  # -1 to 1
            strength -= bb_signal * 0.2  # Invert: low %B = buy signal
            factors += 0.2

        if factors > 0:
            strength = strength / factors

        # Clamp to -1 to 1
        return max(-1.0, min(1.0, strength))

    def get_last_values(self, count: int = 20) -> List[IndicatorData]:
        """Get last N calculated indicator values"""
        # Recalculate for last N prices
        if len(self._price_history) < count:
            count = len(self._price_history)

        return [self._calculate(p) for p in self._price_history[-count:]]

    def clear(self):
        """Clear all price history"""
        self._price_history.clear()
