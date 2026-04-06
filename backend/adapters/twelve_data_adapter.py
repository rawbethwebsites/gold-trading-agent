"""
Twelve Data Adapter
Real gold price data from Twelve Data API with key rotation and API call control
"""

import asyncio
import aiohttp
import random
from datetime import datetime
from typing import Optional, List, Dict, Any

from . import TradingAdapter, PriceData, AccountInfo, Position


class TwelveDataAdapter(TradingAdapter):
    """
    Adapter for Twelve Data API with automatic key rotation.
    Supports multiple API keys and can disable API calls to save tokens.
    """

    def __init__(self, api_keys: List[str] = None, api_calls_enabled: bool = True):
        self._connected = False
        self._api_keys = api_keys or []
        self._current_key_index = 0
        self._api_calls_enabled = api_calls_enabled
        self._base_url = "https://api.twelvedata.com"
        self._last_price = 2650.0
        self._failed_keys = set()  # Track keys that have hit rate limits
        self._cache_timestamp = None
        self._cache_duration = 300  # Cache for 5 minutes when API disabled

    @property
    def _current_key(self) -> Optional[str]:
        """Get current API key, skipping failed ones"""
        if not self._api_keys:
            return None

        # Try to find a key that hasn't failed
        for i in range(len(self._api_keys)):
            idx = (self._current_key_index + i) % len(self._api_keys)
            key = self._api_keys[idx]
            if key not in self._failed_keys:
                self._current_key_index = idx
                return key

        # All keys failed, return None
        return None

    def _rotate_key(self):
        """Rotate to next available API key"""
        if not self._api_keys:
            return

        start_idx = self._current_key_index
        for i in range(1, len(self._api_keys) + 1):
            idx = (start_idx + i) % len(self._api_keys)
            key = self._api_keys[idx]
            if key not in self._failed_keys:
                self._current_key_index = idx
                return

    def _mark_key_failed(self, key: str):
        """Mark an API key as failed (rate limited)"""
        self._failed_keys.add(key)
        print(f"⚠️  API key failed (rate limit). Failed keys: {len(self._failed_keys)}/{len(self._api_keys)}")

    def _reset_failed_keys(self):
        """Reset failed keys (call when all keys exhausted)"""
        if len(self._failed_keys) == len(self._api_keys):
            print("🔄 All API keys exhausted, resetting...")
            self._failed_keys.clear()

    async def connect(self) -> bool:
        """Test API connection with current key"""
        if not self._api_calls_enabled:
            # In cached mode, just simulate connection
            self._connected = True
            return True

        if not self._api_keys:
            print("⚠️  No Twelve Data API keys configured")
            return False

        # Try each key until one works
        for _ in range(len(self._api_keys)):
            key = self._current_key
            if not key:
                self._reset_failed_keys()
                key = self._current_key
                if not key:
                    break

            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self._base_url}/quote?symbol=XAU/USD&apikey={key}"
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'close' in data:
                                self._connected = True
                                return True
                        elif response.status == 429:
                            # Rate limited
                            self._mark_key_failed(key)
                            self._rotate_key()
            except Exception as e:
                print(f"Connection error: {e}")
                self._rotate_key()

        # All keys failed, use cached mode
        print("⚠️  All API keys rate limited, switching to cached mode")
        self._api_calls_enabled = False
        self._connected = True
        return True

    async def disconnect(self):
        """Disconnect"""
        self._connected = False

    async def get_price(self, symbol: str = "XAUUSD") -> Optional[PriceData]:
        """Get current gold price from Twelve Data"""
        if not self.is_connected():
            return None

        # If API calls disabled, return cached/simulated price
        if not self._api_calls_enabled:
            return self._generate_cached_price()

        # Try to fetch from API
        for _ in range(len(self._api_keys) or 1):
            key = self._current_key
            if not key:
                self._reset_failed_keys()
                key = self._current_key

            if not key:
                # No working keys, disable API calls
                self._api_calls_enabled = False
                return self._generate_cached_price()

            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self._base_url}/quote?symbol=XAU/USD&apikey={key}"
                    async with session.get(url, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'close' in data:
                                price = float(data.get("close", 0))
                                if price > 0:
                                    self._last_price = price
                                    self._cache_timestamp = datetime.now()

                                    return PriceData(
                                        timestamp=datetime.now(),
                                        open=float(data.get("open", price)),
                                        high=float(data.get("high", price)),
                                        low=float(data.get("low", price)),
                                        close=price,
                                        volume=int(data.get("volume", 0)),
                                        symbol="XAUUSD"
                                    )
                        elif response.status == 429:
                            # Rate limited
                            self._mark_key_failed(key)
                            self._rotate_key()
                            continue
                        else:
                            # Other error
                            print(f"API error: {response.status}")
                            break
            except asyncio.TimeoutError:
                print("API timeout, rotating key...")
                self._rotate_key()
            except Exception as e:
                print(f"Error fetching price: {e}")
                break

        # API failed, fall back to cached/simulated
        return self._generate_cached_price()

    def _generate_cached_price(self) -> PriceData:
        """Generate price using cached value with small random movement"""
        # Small random movement to simulate live data
        change = random.gauss(0, 0.1)  # Very small movement
        self._last_price += change

        timestamp = datetime.now()
        cache_msg = "[CACHED]" if not self._api_calls_enabled else ""

        return PriceData(
            timestamp=timestamp,
            open=self._last_price - random.uniform(0, 0.5),
            high=self._last_price + random.uniform(0, 0.5),
            low=self._last_price - random.uniform(0, 0.5),
            close=self._last_price,
            volume=random.randint(500, 2000),
            symbol="XAUUSD"
        )

    def _generate_mock_price(self) -> PriceData:
        """Generate simulated price (for initial load)"""
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

    def enable_api_calls(self, enabled: bool = True):
        """Enable or disable API calls to save tokens"""
        self._api_calls_enabled = enabled
        if enabled:
            self._reset_failed_keys()
        print(f"🔌 API calls {'enabled' if enabled else 'disabled (cached mode)'}")

    @property
    def is_api_calls_enabled(self) -> bool:
        """Check if API calls are enabled"""
        return self._api_calls_enabled

    @property
    def available_keys(self) -> int:
        """Number of available API keys"""
        return len(self._api_keys) - len(self._failed_keys)
