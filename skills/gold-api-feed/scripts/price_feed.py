"""
Gold API Price Feed
Real-time precious metals and cryptocurrency prices
Compatible with Claude Code and OpenClaw MCP
"""

import aiohttp
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict


@dataclass
class PriceData:
    """Price data structure"""
    symbol: str
    name: str
    price: float
    currency: str
    updated_at: datetime
    updated_readable: str


class GoldAPIFeed:
    """
    Real-time price feed from gold-api.com

    Features:
    - 60-second caching to prevent IP blocking
    - Support for XAU, XAG, BTC, ETH, XPD, XPT, HG
    - Async/await compatible
    - Graceful fallback to cached data
    """

    BASE_URL = "https://api.gold-api.com"
    CACHE_DURATION = 60  # seconds

    # Symbol mapping
    ASSETS = {
        "XAU": {"name": "Gold", "type": "Precious Metal"},
        "XAG": {"name": "Silver", "type": "Precious Metal"},
        "BTC": {"name": "Bitcoin", "type": "Cryptocurrency"},
        "ETH": {"name": "Ethereum", "type": "Cryptocurrency"},
        "XPD": {"name": "Palladium", "type": "Precious Metal"},
        "XPT": {"name": "Platinum", "type": "Precious Metal"},
        "HG": {"name": "Copper", "type": "Industrial Metal"},
    }

    def __init__(self):
        self._cache: Dict[str, tuple] = {}  # symbol -> (timestamp, price_data)

    async def get_price(self, symbol: str) -> Optional[PriceData]:
        """
        Fetch current price for symbol

        Args:
            symbol: Asset symbol (XAU, XAG, BTC, ETH, XPD, XPT, HG)

        Returns:
            PriceData object or None if fetch failed
        """
        symbol = symbol.upper()
        now = datetime.now()

        # Check cache
        if symbol in self._cache:
            cached_time, cached_data = self._cache[symbol]
            age = (now - cached_time).total_seconds()
            if age < self.CACHE_DURATION:
                return cached_data

        # Fetch from API
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/price/{symbol}"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()

                        price_data = PriceData(
                            symbol=data["symbol"],
                            name=data["name"],
                            price=float(data["price"]),
                            currency=data["currency"],
                            updated_at=datetime.fromisoformat(data["updatedAt"].replace("Z", "+00:00")),
                            updated_readable=data["updatedAtReadable"]
                        )

                        # Update cache
                        self._cache[symbol] = (now, price_data)
                        return price_data

        except Exception as e:
            print(f"Error fetching {symbol}: {e}")

        # Return cached data even if expired (graceful degradation)
        if symbol in self._cache:
            return self._cache[symbol][1]

        return None

    async def get_all_prices(self) -> Dict[str, PriceData]:
        """Fetch prices for all supported assets"""
        tasks = [self.get_price(symbol) for symbol in self.ASSETS.keys()]
        results = await asyncio.gather(*tasks)

        return {
            symbol: result
            for symbol, result in zip(self.ASSETS.keys(), results)
            if result is not None
        }

    def format_price(self, data: PriceData) -> str:
        """Format price data for display"""
        return f"{data.name} ({data.symbol}/USD): ${data.price:,.2f} USD (updated {data.updated_readable})"

    async def get_gold_price(self) -> Optional[PriceData]:
        """Convenience method for gold price"""
        return await self.get_price("XAU")

    async def get_bitcoin_price(self) -> Optional[PriceData]:
        """Convenience method for bitcoin price"""
        return await self.get_price("BTC")

    async def get_silver_price(self) -> Optional[PriceData]:
        """Convenience method for silver price"""
        return await self.get_price("XAG")


# Sync wrapper for easy use
def get_price_sync(symbol: str) -> Optional[PriceData]:
    """Synchronous wrapper for get_price"""
    feed = GoldAPIFeed()
    return asyncio.run(feed.get_price(symbol))


def get_all_prices_sync() -> Dict[str, PriceData]:
    """Synchronous wrapper for get_all_prices"""
    feed = GoldAPIFeed()
    return asyncio.run(feed.get_all_prices())


if __name__ == "__main__":
    # Test the feed
    async def test():
        feed = GoldAPIFeed()

        print("=== Gold API Price Feed Test ===\n")

        # Get all prices
        prices = await feed.get_all_prices()

        for symbol, data in prices.items():
            print(feed.format_price(data))

        print("\n=== Individual Asset Test ===\n")

        # Get individual prices
        gold = await feed.get_gold_price()
        if gold:
            print(f"Gold: ${gold.price:,.2f}")

        bitcoin = await feed.get_bitcoin_price()
        if bitcoin:
            print(f"Bitcoin: ${bitcoin.price:,.2f}")

    asyncio.run(test())
