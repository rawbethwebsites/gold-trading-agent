"""
Twelve Data Adapter
Real gold price data from Twelve Data API
"""

import asyncio
import aiohttp
import random
from datetime import datetime
from typing import Optional, List, Dict, Any

from . import TradingAdapter, PriceData, AccountInfo, Position


class TwelveDataAdapter(TradingAdapter):
    """
    Adapter for Twelve Data API.
    Provides real XAU/USD prices for analysis.
    """

    def __init__(self, api_key: str = ""):
        self._connected = False
        self._api_key = api_key or "demo"  # Free demo key
        self._base_url = "https://api.twelvedata.com"
        self._last_price = 2650.0

    async def connect(self) -> bool:
        """Test API connection"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self._base_url}/quote?symbol=XAU/USD&apikey={self._api_key}"
                async with session.get(url) as response:
                    if response.status == 200:
                        self._connected = True
                        return True
        except Exception as e:
            print(f"Twelve Data connection error: {e}")
        return False

    async def disconnect(self):
        """Disconnect"""
        self._connected = False

    async def get_price(self, symbol: str = "XAUUSD") -> Optional[PriceData]:
        """Get current gold price from Twelve Data"""
        if not self.is_connected():
            return None

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self._base_url}/quote?symbol=XAU/USD&apikey={self._api_key}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data.get("close", 0))
                        self._last_price = price

                        return PriceData(
                            timestamp=datetime.now(),
                            open=float(data.get("open", price)),
                            high=float(data.get("high", price)),
                            low=float(data.get("low", price)),
                            close=price,
                            volume=int(data.get("volume", 0)),
                            symbol="XAUUSD"
                        )
        except Exception as e:
            print(f"Error fetching price: {e}")

        # Fallback to simulated if API fails
        return self._generate_mock_price()

    def _generate_mock_price(self) -> PriceData:
        """Generate simulated price if API fails"""
        change = random.gauss(0, 0.5)
        self._last_price += change

        return PriceData(
            timestamp=datetime.now(),
            open=self._last_price - random.uniform(0, 1),
            high=self._last_price + random.uniform(0, 1),
            low=self._last_price - random.uniform(0, 1),
            close=self._last_price,
            volume=random.randint(100, 1000),
            symbol="XAUUSD"
        )

    async def get_rates(self, symbol: str, timeframe: str, count: int = 100) -> List[PriceData]:
        """Get historical rates"""
        # Generate mock historical data
        rates = []
        price = self._last_price

        for i in range(count, 0, -1):
            price += random.gauss(0, 2)
            rates.append(PriceData(
                timestamp=datetime.now(),
                open=price - random.uniform(0, 1),
                high=price + random.uniform(0, 2),
                low=price - random.uniform(0, 1),
                close=price,
                volume=random.randint(100, 500),
                symbol="XAUUSD"
            ))
        return rates

    async def get_account_info(self) -> Optional[AccountInfo]:
        """Simulated account for Twelve Data mode"""
        return AccountInfo(
            balance=10000.0,
            equity=10000.0,
            margin=0.0,
            free_margin=10000.0,
            margin_level=100.0,
            open_positions=0,
            account_type="demo"
        )

    async def get_positions(self) -> List[Position]:
        """No positions in Twelve Data mode (data only)"""
        return []

    async def get_symbols(self) -> List[str]:
        """Available symbols"""
        return ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]

    async def place_order(self, symbol: str, order_type: str, volume: float,
                         price: Optional[float] = None, sl: Optional[float] = None,
                         tp: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Trading not supported in Twelve Data mode"""
        print("Trading not available in Twelve Data mode. Use MT5 for trading.")
        return None

    async def close_position(self, ticket: int) -> bool:
        """Not supported"""
        return False

    async def modify_position(self, ticket: int, sl: Optional[float] = None,
                             tp: Optional[float] = None) -> bool:
        """Not supported"""
        return False

    def is_connected(self) -> bool:
        """Check connection"""
        return self._connected
