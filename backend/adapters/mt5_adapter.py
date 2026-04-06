"""
MetaTrader 5 Local Adapter
Connects to local MT5 terminal using official MetaTrader5 Python package
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

try:
    from . import TradingAdapter, PriceData, AccountInfo, Position
    from ..config import config
except ImportError:
    # For direct import
    from adapters import TradingAdapter, PriceData, AccountInfo, Position
    from config import config

logger = logging.getLogger(__name__)

# Try to import MT5 package
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 package not installed. Run: pip install MetaTrader5")


class MT5Adapter(TradingAdapter):
    """
    Local MT5 adapter - connects to desktop terminal
    Primary data source for Exness trading
    """

    TIMEFRAME_MAP = {
        "M1": 1,
        "M5": 5,
        "M15": 15,
        "M30": 30,
        "H1": 60,
        "H4": 240,
        "D1": 1440,
        "W1": 10080,
    }

    def __init__(self):
        self._connected = False
        self._initialized = False

    async def connect(self) -> bool:
        """Initialize and connect to MT5 terminal"""
        if not MT5_AVAILABLE:
            logger.error("MetaTrader5 package not available")
            return False

        try:
            # TODO: User needs to verify MT5 terminal path
            # Attempt initialization
            init_path = config.mt5.terminal_path

            if init_path:
                initialized = mt5.initialize(
                    path=init_path,
                    login=config.account.account_number,
                    password=config.account.account_password,
                    server=config.account.server
                )
            else:
                initialized = mt5.initialize()

            if not initialized:
                error = mt5.last_error()
                logger.error(f"MT5 initialization failed: {error}")
                self._initialized = False
                return False

            self._initialized = True

            # Check if already logged in
            account_info = mt5.account_info()
            if account_info is None:
                logger.warning("MT5 not logged in. Please login manually in the terminal")
                # TODO: User needs to login to Exness demo in MT5 terminal
                return False

            logger.info(f"MT5 connected: {account_info.login} on {account_info.server}")
            self._connected = True
            return True

        except Exception as e:
            logger.error(f"MT5 connection error: {e}")
            return False

    async def disconnect(self):
        """Shutdown MT5 connection"""
        if MT5_AVAILABLE and self._initialized:
            mt5.shutdown()
            self._connected = False
            self._initialized = False
            logger.info("MT5 disconnected")

    async def get_price(self, symbol: str) -> Optional[PriceData]:
        """Get current tick price"""
        if not self.is_connected():
            return None

        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None

            return PriceData(
                timestamp=datetime.now(),
                open=tick.open,
                high=tick.high,
                low=tick.low,
                close=tick.last,
                volume=tick.volume,
                symbol=symbol
            )
        except Exception as e:
            logger.error(f"Error getting price: {e}")
            return None

    async def get_rates(self, symbol: str, timeframe: str, count: int = 100) -> List[PriceData]:
        """Get historical rates"""
        if not self.is_connected():
            return []

        tf = self.TIMEFRAME_MAP.get(timeframe, 60)

        try:
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
            if rates is None:
                return []

            return [
                PriceData(
                    timestamp=datetime.fromtimestamp(r[0]),
                    open=r[1],
                    high=r[2],
                    low=r[3],
                    close=r[4],
                    volume=r[5],
                    symbol=symbol
                )
                for r in rates
            ]
        except Exception as e:
            logger.error(f"Error getting rates: {e}")
            return []

    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        if not self.is_connected():
            return None

        try:
            info = mt5.account_info()
            if info is None:
                return None

            return AccountInfo(
                balance=info.balance,
                equity=info.equity,
                margin=info.margin,
                free_margin=info.margin_free,
                margin_level=info.margin_level,
                open_positions=len(mt5.positions_get()),
                account_type="demo" if info.trade_mode == 0 else "real"
            )
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    async def get_positions(self) -> List[Position]:
        """Get open positions"""
        if not self.is_connected():
            return []

        try:
            positions = mt5.positions_get()
            if positions is None:
                return []

            return [
                Position(
                    ticket=p.ticket,
                    symbol=p.symbol,
                    type="buy" if p.type == 0 else "sell",
                    volume=p.volume,
                    open_price=p.price_open,
                    current_price=p.price_current,
                    profit=p.profit,
                    swap=p.swap,
                    open_time=datetime.fromtimestamp(p.time)
                )
                for p in positions
            ]
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    async def get_symbols(self) -> List[str]:
        """Get available symbols"""
        if not self.is_connected():
            return []

        try:
            symbols = mt5.symbols_get()
            if symbols is None:
                return []
            return [s.name for s in symbols]
        except Exception as e:
            logger.error(f"Error getting symbols: {e}")
            return []

    async def place_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Place a trade order (only if trading enabled)"""
        if not self.is_connected():
            return None

        if not config.can_trade:
            logger.warning("Trading not enabled. Set ENABLE_TRADING=true and ENABLE_DEMO_TRADES=true")
            return None

        # Safety check: max positions
        positions = await self.get_positions()
        if len(positions) >= config.trading.max_open_positions:
            logger.warning(f"Max positions reached: {config.trading.max_open_positions}")
            return None

        try:
            # Build order request
            order = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL,
                "price": price or mt5.symbol_info_tick(symbol).ask,
                "deviation": 10,
                "magic": 234000,  # Our EA ID
                "comment": "GoldAgent",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            if sl:
                order["sl"] = sl
            if tp:
                order["tp"] = tp

            result = mt5.order_send(order)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.retcode}")
                return None

            return {
                "ticket": result.order,
                "volume": result.volume,
                "price": result.price,
                "symbol": symbol,
                "type": order_type
            }

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None

    async def close_position(self, ticket: int) -> bool:
        """Close a position"""
        if not self.is_connected():
            return False

        if not config.can_trade:
            logger.warning("Trading not enabled")
            return False

        try:
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                return False

            pos = position[0]

            # Create close order
            close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else mt5.symbol_info_tick(pos.symbol).ask

            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": close_type,
                "position": ticket,
                "price": price,
                "deviation": 10,
                "magic": 234000,
                "comment": "GoldAgent Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(close_request)
            return result.retcode == mt5.TRADE_RETCODE_DONE

        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False

    async def modify_position(self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None) -> bool:
        """Modify position SL/TP"""
        if not self.is_connected():
            return False

        if not config.can_trade:
            logger.warning("Trading not enabled")
            return False

        try:
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                return False

            pos = position[0]

            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": ticket,
                "sl": sl if sl else pos.sl,
                "tp": tp if tp else pos.tp,
            }

            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE

        except Exception as e:
            logger.error(f"Error modifying position: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if MT5 is connected and initialized"""
        if not MT5_AVAILABLE or not self._initialized:
            return False
        return mt5.terminal_info() is not None

