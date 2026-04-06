"""
Adapter pattern for data sources
Supports: Local MT5 (default), MetaApi (optional), Mock (fallback)
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PriceData:
    """Standardized price data structure"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    symbol: str


@dataclass
class AccountInfo:
    """Account information"""
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    open_positions: int
    account_type: str  # demo/real


@dataclass
class Position:
    """Open position data"""
    ticket: int
    symbol: str
    type: str  # buy/sell
    volume: float
    open_price: float
    current_price: float
    profit: float
    swap: float
    open_time: datetime


class DataAdapter(ABC):
    """Abstract base class for data adapters"""

    @abstractmethod
    async def connect(self) -> bool:
        """Connect to data source"""
        pass

    @abstractmethod
    async def disconnect(self):
        """Disconnect from data source"""
        pass

    @abstractmethod
    async def get_price(self, symbol: str) -> Optional[PriceData]:
        """Get current price for symbol"""
        pass

    @abstractmethod
    async def get_rates(self, symbol: str, timeframe: str, count: int = 100) -> List[PriceData]:
        """Get historical rates"""
        pass

    @abstractmethod
    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        pass

    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get open positions"""
        pass

    @abstractmethod
    async def get_symbols(self) -> List[str]:
        """Get available symbols"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected"""
        pass


class TradingAdapter(DataAdapter):
    """Extended adapter with trading capabilities"""

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Place a trade order"""
        pass

    @abstractmethod
    async def close_position(self, ticket: int) -> bool:
        """Close an open position"""
        pass

    @abstractmethod
    async def modify_position(
        self,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> bool:
        """Modify position SL/TP"""
        pass


# Import implementations after base classes are defined to avoid circular imports
from .mt5_adapter import MT5Adapter
from .mock_adapter import MockAdapter
from .twelve_data_adapter import TwelveDataAdapter
from .demo_trading_adapter import DemoTradingAdapter

__all__ = [
    "DataAdapter",
    "TradingAdapter",
    "PriceData",
    "AccountInfo",
    "Position",
    "MT5Adapter",
    "MockAdapter",
    "TwelveDataAdapter",
    "DemoTradingAdapter",
]
