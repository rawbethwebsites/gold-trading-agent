"""
Signal Engine
Generates BUY/SELL/HOLD signals from technical indicators
Uses confluence algorithm requiring 2+ indicators to agree
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from .indicator_engine import IndicatorData


class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Signal:
    """Trading signal with confidence and reasoning"""
    timestamp: datetime
    symbol: str
    type: SignalType
    price: float
    confidence: float  # 0.0 to 1.0
    strength: float  # -1.0 to 1.0 (signal strength)
    reasons: List[str]  # Why this signal was generated
    indicators: Dict[str, Any]  # Snapshot of indicator values
    suggested_sl: Optional[float] = None  # Suggested stop loss
    suggested_tp: Optional[float] = None  # Suggested take profit


class SignalEngine:
    """
    Generate trading signals based on indicator confluence.
    Requires 2+ indicators to agree before generating a signal.
    """

    # Signal thresholds
    CONFIDENCE_THRESHOLD = 0.6  # Minimum confidence to generate signal
    MIN_INDICATORS_AGREE = 2  # Minimum indicators that must agree

    # RSI thresholds for gold
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    RSI_NEUTRAL_LOW = 40
    RSI_NEUTRAL_HIGH = 60

    # Signal strength thresholds
    STRONG_BUY_THRESHOLD = 0.6
    STRONG_SELL_THRESHOLD = -0.6

    def __init__(self):
        self._last_signal: Optional[Signal] = None
        self._signal_cooldown_bars = 3  # Bars to wait between signals
        self._bars_since_last_signal = 0
        self._signal_history: List[Signal] = []
        self._max_history = 100

    def process(self, indicator: IndicatorData) -> Optional[Signal]:
        """
        Process indicator data and generate signal if conditions met.
        Returns Signal or None if no signal.
        """
        self._bars_since_last_signal += 1

        # Gather buy/sell votes from each indicator
        buy_votes = []
        sell_votes = []

        # 1. RSI Analysis
        rsi_vote = self._analyze_rsi(indicator)
        if rsi_vote == "buy":
            buy_votes.append("RSI oversold")
        elif rsi_vote == "sell":
            sell_votes.append("RSI overbought")

        # 2. MACD Analysis
        macd_vote = self._analyze_macd(indicator)
        if macd_vote == "buy":
            buy_votes.append("MACD bullish crossover")
        elif macd_vote == "sell":
            sell_votes.append("MACD bearish crossover")

        # 3. EMA Trend Analysis
        ema_vote = self._analyze_ema(indicator)
        if ema_vote == "buy":
            buy_votes.append("EMA bullish alignment")
        elif ema_vote == "sell":
            sell_votes.append("EMA bearish alignment")

        # 4. Bollinger Bands Analysis
        bb_vote = self._analyze_bollinger(indicator)
        if bb_vote == "buy":
            buy_votes.append("Price at lower band")
        elif bb_vote == "sell":
            sell_votes.append("Price at upper band")

        # 5. Overall Signal Strength
        if indicator.signal_strength >= self.STRONG_BUY_THRESHOLD:
            buy_votes.append("Strong composite signal")
        elif indicator.signal_strength <= self.STRONG_SELL_THRESHOLD:
            sell_votes.append("Strong composite signal")

        # Determine signal based on confluence
        signal = self._determine_signal(
            indicator, buy_votes, sell_votes
        )

        if signal:
            self._last_signal = signal
            self._bars_since_last_signal = 0
            self._signal_history.append(signal)

            # Trim history
            if len(self._signal_history) > self._max_history:
                self._signal_history = self._signal_history[-self._max_history:]

        return signal

    def _analyze_rsi(self, indicator: IndicatorData) -> str:
        """Analyze RSI for buy/sell signals"""
        if indicator.rsi_14 is None:
            return "neutral"

        if indicator.rsi_14 < self.RSI_OVERSOLD:
            return "buy"
        elif indicator.rsi_14 > self.RSI_OVERBOUGHT:
            return "sell"

        return "neutral"

    def _analyze_macd(self, indicator: IndicatorData) -> str:
        """Analyze MACD for buy/sell signals"""
        if indicator.macd is None or indicator.macd_signal is None:
            return "neutral"

        # Bullish: MACD above signal and histogram positive
        if indicator.macd > indicator.macd_signal and indicator.macd_histogram > 0:
            return "buy"
        # Bearish: MACD below signal and histogram negative
        elif indicator.macd < indicator.macd_signal and indicator.macd_histogram < 0:
            return "sell"

        return "neutral"

    def _analyze_ema(self, indicator: IndicatorData) -> str:
        """Analyze EMA alignment for trend direction"""
        if indicator.ema_9 is None or indicator.ema_21 is None:
            return "neutral"

        # Bullish alignment: EMA9 > EMA21 > SMA50
        if indicator.ema_9 > indicator.ema_21:
            if indicator.sma_50 and indicator.ema_21 > indicator.sma_50:
                return "buy"
            return "buy_weak"

        # Bearish alignment: EMA9 < EMA21 < SMA50
        elif indicator.ema_9 < indicator.ema_21:
            if indicator.sma_50 and indicator.ema_21 < indicator.sma_50:
                return "sell"
            return "sell_weak"

        return "neutral"

    def _analyze_bollinger(self, indicator: IndicatorData) -> str:
        """Analyze Bollinger Bands for mean reversion signals"""
        if indicator.bb_percent is None:
            return "neutral"

        # Price below lower band (oversold)
        if indicator.bb_percent < 0:
            return "buy"
        # Price above upper band (overbought)
        elif indicator.bb_percent > 1:
            return "sell"

        return "neutral"

    def _determine_signal(
        self,
        indicator: IndicatorData,
        buy_votes: List[str],
        sell_votes: List[str]
    ) -> Optional[Signal]:
        """
        Determine final signal based on confluence of indicators.
        Requires MIN_INDICATORS_AGREE to generate a signal.
        """
        # Check cooldown
        if self._bars_since_last_signal < self._signal_cooldown_bars:
            return None

        # Check for signal reversal (different from last signal)
        if self._last_signal:
            last_type = self._last_signal.type
        else:
            last_type = None

        # Count strong votes (exclude weak)
        strong_buy = [v for v in buy_votes if "weak" not in v]
        strong_sell = [v for v in sell_votes if "weak" not in v]

        signal_type = None
        reasons = []
        confidence = 0.0

        # Require minimum confluence
        if len(strong_buy) >= self.MIN_INDICATORS_AGREE:
            signal_type = SignalType.BUY
            reasons = strong_buy
            confidence = min(len(strong_buy) / 4.0, 1.0)  # Max confidence at 4+ indicators

        elif len(strong_sell) >= self.MIN_INDICATORS_AGREE:
            signal_type = SignalType.SELL
            reasons = strong_sell
            confidence = min(len(strong_sell) / 4.0, 1.0)

        # No signal if not enough confluence
        if signal_type is None or confidence < self.CONFIDENCE_THRESHOLD:
            return None

        # Calculate suggested SL/TP based on ATR
        sl, tp = self._calculate_sl_tp(indicator, signal_type)

        return Signal(
            timestamp=indicator.timestamp,
            symbol=indicator.symbol,
            type=signal_type,
            price=indicator.price,
            confidence=confidence,
            strength=indicator.signal_strength,
            reasons=reasons,
            indicators=self._snapshot_indicators(indicator),
            suggested_sl=sl,
            suggested_tp=tp
        )

    def _calculate_sl_tp(
        self,
        indicator: IndicatorData,
        signal_type: SignalType
    ) -> tuple:
        """Calculate suggested stop loss and take profit based on ATR"""
        if indicator.atr_14 is None:
            return None, None

        price = indicator.price
        atr = indicator.atr_14

        # Use 2x ATR for SL, 4x ATR for TP (1:2 risk/reward)
        if signal_type == SignalType.BUY:
            sl = price - (2 * atr)
            tp = price + (4 * atr)
        else:
            sl = price + (2 * atr)
            tp = price - (4 * atr)

        return round(sl, 2), round(tp, 2)

    def _snapshot_indicators(self, indicator: IndicatorData) -> Dict[str, Any]:
        """Create snapshot of relevant indicator values"""
        return {
            "rsi": indicator.rsi_14,
            "macd": indicator.macd,
            "macd_histogram": indicator.macd_histogram,
            "ema_9": indicator.ema_9,
            "ema_21": indicator.ema_21,
            "sma_50": indicator.sma_50,
            "bb_percent": indicator.bb_percent,
            "atr": indicator.atr_14,
        }

    def get_recent_signals(self, count: int = 10) -> List[Signal]:
        """Get recent signal history"""
        return self._signal_history[-count:]

    def get_last_signal(self) -> Optional[Signal]:
        """Get the most recent signal"""
        return self._last_signal

    def clear_history(self):
        """Clear signal history"""
        self._signal_history.clear()
        self._last_signal = None
