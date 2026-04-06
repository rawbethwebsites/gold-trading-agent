"""
Trading Service
Orchestrates adapters, indicator engine, signal engine, and risk manager
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

try:
    from ..config import config
    from ..adapters import TradingAdapter, PriceData, AccountInfo, Position
    from ..core import IndicatorEngine, SignalEngine, RiskManager, Signal, IndicatorData
except ImportError:
    from config import config
    from adapters import TradingAdapter, PriceData, AccountInfo, Position
    from core import IndicatorEngine, SignalEngine, RiskManager, Signal, IndicatorData

logger = logging.getLogger(__name__)


@dataclass
class TradingState:
    """Current state of the trading system"""
    connected: bool = False
    symbol: str = ""
    last_price: Optional[PriceData] = None
    last_indicator: Optional[IndicatorData] = None
    last_signal: Optional[Signal] = None
    account: Optional[AccountInfo] = None
    positions: List[Position] = None
    is_trading: bool = False
    error: Optional[str] = None

    def __post_init__(self):
        if self.positions is None:
            self.positions = []


class TradingService:
    """
    Main service that coordinates all trading operations.
    Polls MT5 data, runs indicators, generates signals, executes trades.
    """

    def __init__(self, adapter: TradingAdapter):
        self.adapter = adapter
        self.indicator_engine = IndicatorEngine()
        self.signal_engine = SignalEngine()
        self.risk_manager = RiskManager()

        self.state = TradingState()
        self.state.symbol = config.mt5.symbol

        self._running = False
        self._polling_interval = config.app.polling_interval

        # Store indicator history for charts
        self._indicator_history: List[IndicatorData] = []
        self._max_history = 200

        # Trade history for stats
        self._trade_history: List[Dict[str, Any]] = []

    async def start(self) -> bool:
        """Initialize and start the trading service"""
        logger.info("Starting Trading Service...")

        # Connect to MT5
        connected = await self.adapter.connect()
        if not connected:
            self.state.error = "Failed to connect to MT5"
            logger.error(self.state.error)
            return False

        self.state.connected = True
        logger.info("Trading Service started successfully")

        # Load initial history for indicators
        await self._load_initial_history()

        # Start polling loop
        self._running = True
        asyncio.create_task(self._polling_loop())

        return True

    async def stop(self):
        """Stop the trading service"""
        logger.info("Stopping Trading Service...")
        self._running = False
        await self.adapter.disconnect()
        self.state.connected = False
        self.state.is_trading = False
        logger.info("Trading Service stopped")

    async def _load_initial_history(self):
        """Load historical data for indicator warmup"""
        logger.info(f"Loading {self.state.symbol} history...")

        rates = await self.adapter.get_rates(
            self.state.symbol,
            config.mt5.timeframe,
            count=100
        )

        if rates:
            self.indicator_engine.update_batch(rates)
            logger.info(f"Loaded {len(rates)} historical bars")
        else:
            logger.warning("Could not load historical data")

    async def _polling_loop(self):
        """Main polling loop - runs continuously"""
        logger.info(f"Starting polling loop (interval: {self._polling_interval}s)")

        while self._running:
            try:
                await self._tick()
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                self.state.error = str(e)

            await asyncio.sleep(self._polling_interval)

        logger.info("Polling loop stopped")

    async def _tick(self):
        """Process one tick - get price, update indicators, check signals"""
        # Get current price
        price = await self.adapter.get_price(self.state.symbol)
        if price is None:
            logger.warning("Could not get price data")
            return

        self.state.last_price = price

        # Update indicators
        indicator = self.indicator_engine.update(price)
        self.state.last_indicator = indicator

        # Store in history
        self._indicator_history.append(indicator)
        if len(self._indicator_history) > self._max_history:
            self._indicator_history = self._indicator_history[-self._max_history:]

        # Check for trading signal
        signal = self.signal_engine.process(indicator)
        if signal:
            self.state.last_signal = signal
            logger.info(f"Signal generated: {signal.type.value} @ {signal.price}")
            logger.info(f"  Confidence: {signal.confidence:.2f}, Reasons: {signal.reasons}")

            # Execute trade if signal is strong enough
            await self._execute_signal(signal)

        # Update account and positions
        self.state.account = await self.adapter.get_account_info()
        self.state.positions = await self.adapter.get_positions()

    async def _execute_signal(self, signal: Signal):
        """Execute a trading signal if risk checks pass"""
        if not config.can_trade:
            logger.info("Signal received but trading disabled")
            return

        # Risk check
        risk_check = self.risk_manager.can_trade(
            self.state.account,
            self.state.positions,
            signal.type.value
        )

        if not risk_check.allowed:
            logger.warning(f"Risk check failed: {risk_check.reason}")
            return

        # Place the order
        lot_size = risk_check.adjusted_lot_size or config.trading.default_lot_size

        logger.info(f"Placing {signal.type.value} order: {lot_size} lots @ {signal.price}")

        result = await self.adapter.place_order(
            symbol=signal.symbol,
            order_type=signal.type.value,
            volume=lot_size,
            sl=signal.suggested_sl,
            tp=signal.suggested_tp
        )

        if result:
            logger.info(f"Order placed successfully: Ticket {result['ticket']}")
            self.state.is_trading = True
        else:
            logger.error("Order placement failed")

    # Public API methods for REST endpoints

    def get_status(self) -> Dict[str, Any]:
        """Get current trading status"""
        return {
            "connected": self.state.connected,
            "is_trading": self.state.is_trading,
            "symbol": self.state.symbol,
            "can_trade": config.can_trade,
            "error": self.state.error,
            "active_source": getattr(self.adapter, 'active_source', "Unknown"),
            "last_update": datetime.now().isoformat(),
        }

    def get_price_data(self) -> Optional[Dict[str, Any]]:
        """Get current price data"""
        if self.state.last_price is None:
            return None

        return {
            "timestamp": self.state.last_price.timestamp.isoformat(),
            "symbol": self.state.last_price.symbol,
            "bid": self.state.last_price.close,  # Approximate
            "ask": self.state.last_price.close,
            "open": self.state.last_price.open,
            "high": self.state.last_price.high,
            "low": self.state.last_price.low,
            "close": self.state.last_price.close,
            "volume": self.state.last_price.volume,
        }

    def get_indicator_data(self) -> Optional[Dict[str, Any]]:
        """Get current indicator values"""
        if self.state.last_indicator is None:
            return None

        ind = self.state.last_indicator
        return {
            "timestamp": ind.timestamp.isoformat(),
            "symbol": ind.symbol,
            "price": ind.price,
            "ema_9": ind.ema_9,
            "ema_21": ind.ema_21,
            "sma_50": ind.sma_50,
            "macd": ind.macd,
            "macd_histogram": ind.macd_histogram,
            "rsi_14": ind.rsi_14,
            "bb_upper": ind.bb_upper,
            "bb_lower": ind.bb_lower,
            "bb_percent": ind.bb_percent,
            "atr_14": ind.atr_14,
            "trend": ind.trend,
            "signal_strength": ind.signal_strength,
        }

    def get_account_data(self) -> Optional[Dict[str, Any]]:
        """Get account information"""
        if self.state.account is None:
            return None

        acc = self.state.account
        return {
            "balance": acc.balance,
            "equity": acc.equity,
            "margin": acc.margin,
            "free_margin": acc.free_margin,
            "margin_level": acc.margin_level,
            "open_positions": acc.open_positions,
            "account_type": acc.account_type,
            "can_trade": config.can_trade,
        }

    def get_positions_data(self) -> List[Dict[str, Any]]:
        """Get open positions"""
        return [
            {
                "ticket": p.ticket,
                "symbol": p.symbol,
                "type": p.type,
                "volume": p.volume,
                "open_price": p.open_price,
                "current_price": p.current_price,
                "profit": p.profit,
                "swap": p.swap,
                "open_time": p.open_time.isoformat(),
            }
            for p in self.state.positions
        ]

    def get_last_signal(self) -> Optional[Dict[str, Any]]:
        """Get last generated signal"""
        if self.state.last_signal is None:
            return None

        sig = self.state.last_signal
        return {
            "timestamp": sig.timestamp.isoformat(),
            "symbol": sig.symbol,
            "type": sig.type.value,
            "price": sig.price,
            "confidence": sig.confidence,
            "strength": sig.strength,
            "reasons": sig.reasons,
            "suggested_sl": sig.suggested_sl,
            "suggested_tp": sig.suggested_tp,
            "indicators": sig.indicators,
        }

    async def close_position(self, ticket: int) -> bool:
        """Close a specific position"""
        if not config.can_trade:
            logger.warning("Cannot close position: trading not enabled")
            return False

        return await self.adapter.close_position(ticket)

    async def close_all_positions(self) -> int:
        """Close all open positions"""
        if not config.can_trade:
            logger.warning("Cannot close positions: trading not enabled")
            return 0

        closed = 0
        for position in self.state.positions:
            if await self.adapter.close_position(position.ticket):
                closed += 1

        return closed

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical indicator data for charts"""
        history = self._indicator_history[-limit:] if self._indicator_history else []
        return [
            {
                "timestamp": ind.timestamp.isoformat(),
                "symbol": ind.symbol,
                "price": ind.price,
                "ema_9": ind.ema_9,
                "ema_21": ind.ema_21,
                "sma_50": ind.sma_50,
                "macd": ind.macd,
                "macd_histogram": ind.macd_histogram,
                "rsi_14": ind.rsi_14,
                "bb_upper": ind.bb_upper,
                "bb_lower": ind.bb_lower,
                "bb_percent": ind.bb_percent,
                "atr_14": ind.atr_14,
                "trend": ind.trend,
                "signal_strength": ind.signal_strength,
            }
            for ind in history
        ]

    def get_trade_history(self) -> Dict[str, Any]:
        """Get trade history stats"""
        # Mock trade history for now - in production this would come from adapter
        mock_trades = [
            {"ticket": 1001, "symbol": "XAUUSD", "type": "buy", "volume": 0.01,
             "open_price": 2650.50, "close_price": 2652.30, "profit": 18.00,
             "open_time": "2024-01-15T10:00:00", "close_time": "2024-01-15T12:30:00"},
            {"ticket": 1002, "symbol": "XAUUSD", "type": "sell", "volume": 0.01,
             "open_price": 2655.20, "close_price": 2651.80, "profit": 34.00,
             "open_time": "2024-01-15T14:00:00", "close_time": "2024-01-15T16:45:00"},
            {"ticket": 1003, "symbol": "XAUUSD", "type": "buy", "volume": 0.01,
             "open_price": 2648.00, "close_price": 2645.50, "profit": -25.00,
             "open_time": "2024-01-16T09:00:00", "close_time": "2024-01-16T11:20:00"},
            {"ticket": 1004, "symbol": "XAUUSD", "type": "sell", "volume": 0.01,
             "open_price": 2660.00, "close_price": 2658.50, "profit": 15.00,
             "open_time": "2024-01-16T13:00:00", "close_time": "2024-01-16T15:30:00"},
        ]

        if not mock_trades:
            return {"trades": [], "stats": {"total": 0, "wins": 0, "losses": 0, "win_rate": 0, "total_profit": 0}}

        wins = sum(1 for t in mock_trades if t["profit"] > 0)
        losses = sum(1 for t in mock_trades if t["profit"] <= 0)
        total_profit = sum(t["profit"] for t in mock_trades)
        avg_win = sum(t["profit"] for t in mock_trades if t["profit"] > 0) / wins if wins > 0 else 0
        avg_loss = sum(t["profit"] for t in mock_trades if t["profit"] < 0) / losses if losses > 0 else 0

        return {
            "trades": mock_trades,
            "stats": {
                "total": len(mock_trades),
                "wins": wins,
                "losses": losses,
                "win_rate": round(wins / len(mock_trades) * 100, 1),
                "total_profit": round(total_profit, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
            }
        }

    async def get_rates_for_timeframe(self, timeframe: str, count: int = 100) -> List[PriceData]:
        """Fetch historical rates for a specific timeframe"""
        return await self.adapter.get_rates(self.state.symbol, timeframe, count)
