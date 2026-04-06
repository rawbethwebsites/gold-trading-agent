"""
Mock Adapter
Simulates MT5 data for testing without a live connection
"""

import asyncio
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from . import TradingAdapter, PriceData, AccountInfo, Position


class MockAdapter(TradingAdapter):
    """
    Mock adapter that generates simulated price data.
    Useful for testing the system without MT5 connection.
    """

    def __init__(self):
        self._connected = False
        self._price = 2650.0  # Starting gold price
        self._positions: List[Position] = []
        self._next_ticket = 1000
        self._balance = 10000.0

    async def connect(self) -> bool:
        """Simulate connection"""
        await asyncio.sleep(0.1)  # Simulate connection delay
        self._connected = True
        return True

    async def disconnect(self):
        """Simulate disconnection"""
        self._connected = False

    def _generate_price(self) -> float:
        """Generate realistic gold price movement (random walk)"""
        # Simulate small random movements (gold volatility)
        change = random.gauss(0, 0.5)  # Mean 0, std dev 0.5
        self._price += change
        return round(self._price, 2)

    async def get_price(self, symbol: str) -> Optional[PriceData]:
        """Get simulated current price"""
        if not self.is_connected():
            return None

        price = self._generate_price()
        spread = 0.5  # Typical gold spread

        return PriceData(
            timestamp=datetime.now(),
            open=price - random.uniform(0, 1),
            high=price + random.uniform(0, 1),
            low=price - random.uniform(0, 1),
            close=price,
            volume=random.randint(100, 1000),
            symbol=symbol
        )

    async def get_rates(self, symbol: str, timeframe: str, count: int = 100) -> List[PriceData]:
        """Generate historical rate data"""
        if not self.is_connected():
            return []

        rates = []
        current_price = self._price

        # Generate 100 bars of history
        for i in range(count, 0, -1):
            timestamp = datetime.now() - timedelta(hours=i)
            change = random.gauss(0, 2.0)  # More volatility for historical
            current_price -= change  # Work backwards

            rates.append(PriceData(
                timestamp=timestamp,
                open=current_price - random.uniform(0, 2),
                high=current_price + random.uniform(0, 2),
                low=current_price - random.uniform(0, 2),
                close=current_price,
                volume=random.randint(100, 1000),
                symbol=symbol
            ))

        return rates

    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get simulated account info"""
        if not self.is_connected():
            return None

        # Calculate equity from positions
        position_pnl = sum(p.profit for p in self._positions)
        equity = self._balance + position_pnl
        margin = sum(p.volume * 100 for p in self._positions)  # Rough estimate
        free_margin = equity - margin
        margin_level = (equity / margin * 100) if margin > 0 else 0

        return AccountInfo(
            balance=self._balance,
            equity=equity,
            margin=margin,
            free_margin=free_margin,
            margin_level=margin_level,
            open_positions=len(self._positions),
            account_type="demo"
        )

    async def get_positions(self) -> List[Position]:
        """Get simulated positions"""
        if not self.is_connected():
            return []

        # Update positions with random P&L
        for pos in self._positions:
            price_change = random.gauss(0, 0.1)
            if pos.type == "buy":
                pos.profit += price_change * pos.volume * 100
            else:
                pos.profit -= price_change * pos.volume * 100

        return self._positions

    async def get_symbols(self) -> List[str]:
        """Get available symbols"""
        return ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]

    async def place_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Simulate placing an order"""
        if not self.is_connected():
            return None

        # Create mock position
        current_price = self._price
        entry_price = price or current_price

        position = Position(
            ticket=self._next_ticket,
            symbol=symbol,
            type=order_type,
            volume=volume,
            open_price=entry_price,
            current_price=current_price,
            profit=0.0,
            swap=0.0,
            open_time=datetime.now()
        )

        self._positions.append(position)
        self._next_ticket += 1

        return {
            "ticket": position.ticket,
            "volume": volume,
            "price": entry_price,
            "symbol": symbol,
            "type": order_type
        }

    async def close_position(self, ticket: int) -> bool:
        """Simulate closing a position"""
        if not self.is_connected():
            return False

        for i, pos in enumerate(self._positions):
            if pos.ticket == ticket:
                # Realize profit/loss
                self._balance += pos.profit
                self._positions.pop(i)
                return True

        return False

    async def modify_position(self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None) -> bool:
        """Simulate modifying position SL/TP"""
        return True  # Always succeed in mock mode

    def is_connected(self) -> bool:
        """Check if mock is connected"""
        return self._connected


# For backwards compatibility with old tests
class GoldDataFeed:
    """Legacy wrapper for tests - delegates to MockAdapter"""

    def __init__(self):
        self.adapter = MockAdapter()
        self.is_running = False
        self.latest_price = None
        self.connected_clients = []
        self.ta = None  # Would be TechnicalAnalysis in old code

    async def start_feed(self):
        await self.adapter.connect()
        self.is_running = True

    def stop(self):
        self.is_running = False

    async def fetch_price(self):
        price = await self.adapter.get_price("XAUUSD")
        self.latest_price = price
        return price
