"""
Demo Trading Adapter
In-built demo trading simulator - no MT5 required!
Uses real price data from public APIs, simulates trades internally.
"""

import asyncio
import random
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from . import TradingAdapter, PriceData, AccountInfo, Position
from .public_api_adapter import PublicApiAdapter


@dataclass
class DemoPosition:
    """Internal demo position tracking"""
    ticket: int
    symbol: str
    type: str  # buy/sell
    volume: float
    open_price: float
    current_price: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    open_time: datetime = field(default_factory=datetime.now)
    swap: float = 0.0

    def calculate_profit(self) -> float:
        """Calculate unrealized P&L"""
        point_value = 1.0  # $1 per point for XAUUSD standard lot
        volume_units = self.volume * 100  # Convert lots to units

        if self.type == "buy":
            price_diff = self.current_price - self.open_price
        else:  # sell
            price_diff = self.open_price - self.current_price

        return price_diff * volume_units * point_value


class DemoTradingAdapter(TradingAdapter):
    """
    Demo trading adapter - simulated trading with real price data.
    No MT5 required! Uses public APIs for prices, tracks trades internally.
    """

    def __init__(self, initial_balance: float = 10000.0, symbol: str = "XAUUSD", api_keys: list = None):
        # Price data provider (Public APIs with fallbacks)
        self._price_adapter = PublicApiAdapter(
            api_keys=api_keys or [],
            api_calls_enabled=True
        )

        # Demo account state
        self._balance = initial_balance
        self._equity = initial_balance
        self._initial_balance = initial_balance
        self._symbol = symbol
        self._connected = False
        self._next_ticket = 1000
        self._positions: Dict[int, DemoPosition] = {}
        self._trade_history: List[Dict] = []

        # Demo settings
        self._spread = 0.5  # 50 cent spread for XAUUSD
        self._swap_rate = -0.5  # Negative swap (cost to hold overnight)
        self._commission = 0.0  # No commission in demo

    async def connect(self) -> bool:
        """Connect to price feed - no MT5 needed!"""
        print("🔗 Connecting to Demo Trading Mode...")
        print(f"   Initial Balance: ${self._balance:,.2f}")
        print(f"   Symbol: {self._symbol}")
        print("   ✨ No MT5 required - trading simulation active")

        # Connect to price feed
        price_connected = await self._price_adapter.connect()
        if not price_connected:
            print("⚠️  Warning: Could not connect to price feed")
            return False

        self._connected = True
        print("✅ Demo Trading Mode connected!")
        return True

    async def disconnect(self):
        """Disconnect"""
        self._connected = False
        await self._price_adapter.disconnect()
        print("👋 Demo Trading Mode disconnected")

    async def get_price(self, symbol: str = "XAUUSD") -> Optional[PriceData]:
        """Get current price from public APIs"""
        return await self._price_adapter.get_price(symbol)

    async def get_rates(self, symbol: str, timeframe: str, count: int = 100) -> List[PriceData]:
        """Get historical rates"""
        return await self._price_adapter.get_rates(symbol, timeframe, count)

    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get demo account info with live P&L"""
        if not self._connected:
            return None

        # Update equity based on current positions
        await self._update_equity()

        # Calculate margin usage
        margin_used = sum(
            pos.volume * 1000 for pos in self._positions.values()  # $1000 margin per lot
        )

        margin_level = (self._equity / margin_used * 100) if margin_used > 0 else 100.0

        return AccountInfo(
            balance=self._balance,
            equity=self._equity,
            margin=margin_used,
            free_margin=self._equity - margin_used,
            margin_level=margin_level,
            open_positions=len(self._positions),
            account_type="demo"
        )

    async def get_positions(self) -> List[Position]:
        """Get open demo positions with live P&L"""
        if not self._connected:
            return []

        current_price = await self._get_current_price()
        if not current_price:
            return []

        positions = []
        for demo_pos in self._positions.values():
            demo_pos.current_price = current_price.close
            profit = demo_pos.calculate_profit()

            positions.append(Position(
                ticket=demo_pos.ticket,
                symbol=demo_pos.symbol,
                type=demo_pos.type,
                volume=demo_pos.volume,
                open_price=demo_pos.open_price,
                current_price=demo_pos.current_price,
                profit=profit,
                swap=demo_pos.swap,
                open_time=demo_pos.open_time
            ))

        return positions

    async def place_order(
        self,
        symbol: str,
        order_type: str,  # buy/sell
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Place a demo trade"""
        if not self._connected:
            return None

        # Get current price
        current_price_data = await self._get_current_price()
        if not current_price_data:
            return None

        # Calculate entry price (with spread)
        if order_type == "buy":
            entry_price = current_price_data.close + self._spread
        else:  # sell
            entry_price = current_price_data.close - self._spread

        # Check margin requirement ($1000 per lot)
        margin_required = volume * 1000
        await self._update_equity()

        if margin_required > self._equity * 0.9:  # 90% margin limit
            print(f"❌ Order rejected: Insufficient margin")
            return None

        # Create position
        ticket = self._next_ticket
        self._next_ticket += 1

        position = DemoPosition(
            ticket=ticket,
            symbol=symbol,
            type=order_type,
            volume=volume,
            open_price=entry_price,
            current_price=entry_price,
            sl=sl,
            tp=tp
        )

        self._positions[ticket] = position

        # Deduct margin
        self._balance -= margin_required

        print(f"✅ Demo order executed:")
        print(f"   Ticket: #{ticket}")
        print(f"   Type: {order_type.upper()}")
        print(f"   Volume: {volume} lots")
        print(f"   Entry: ${entry_price:.2f}")
        print(f"   SL: ${sl:.2f}" if sl else "   SL: None")
        print(f"   TP: ${tp:.2f}" if tp else "   TP: None")

        # Record trade
        self._trade_history.append({
            "ticket": ticket,
            "symbol": symbol,
            "type": order_type,
            "volume": volume,
            "open_price": entry_price,
            "time": datetime.now(),
            "action": "open"
        })

        return {
            "ticket": ticket,
            "symbol": symbol,
            "type": order_type,
            "volume": volume,
            "price": entry_price,
            "sl": sl,
            "tp": tp
        }

    async def close_position(self, ticket: int) -> bool:
        """Close a demo position"""
        if ticket not in self._positions:
            return False

        position = self._positions[ticket]
        current_price_data = await self._get_current_price()
        if not current_price_data:
            return False

        # Calculate closing price
        if position.type == "buy":
            close_price = current_price_data.close - self._spread
        else:
            close_price = current_price_data.close + self._spread

        position.current_price = close_price
        profit = position.calculate_profit()

        # Return margin + profit
        margin_returned = position.volume * 1000
        self._balance += margin_returned + profit

        print(f"✅ Position #{ticket} closed:")
        print(f"   Profit: ${profit:+.2f}")
        print(f"   Balance: ${self._balance:,.2f}")

        # Record trade
        self._trade_history.append({
            "ticket": ticket,
            "symbol": position.symbol,
            "type": position.type,
            "volume": position.volume,
            "close_price": close_price,
            "profit": profit,
            "time": datetime.now(),
            "action": "close"
        })

        del self._positions[ticket]
        return True

    async def modify_position(
        self,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> bool:
        """Modify SL/TP on a position"""
        if ticket not in self._positions:
            return False

        position = self._positions[ticket]
        if sl is not None:
            position.sl = sl
        if tp is not None:
            position.tp = tp

        print(f"✅ Position #{ticket} modified:")
        print(f"   SL: ${position.sl:.2f}" if position.sl else "   SL: None")
        print(f"   TP: ${position.tp:.2f}" if position.tp else "   TP: None")

        return True

    async def get_symbols(self) -> List[str]:
        """Get available symbols"""
        return ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"]

    def is_connected(self) -> bool:
        """Check if connected"""
        return self._connected

    # Helper methods

    async def _get_current_price(self) -> Optional[PriceData]:
        """Get current price from price adapter"""
        return await self._price_adapter.get_price(self._symbol)

    async def _update_equity(self):
        """Recalculate equity based on current positions"""
        current_price_data = await self._get_current_price()
        if not current_price_data:
            return

        unrealized_pnl = 0.0
        for pos in self._positions.values():
            pos.current_price = current_price_data.close
            unrealized_pnl += pos.calculate_profit()

        self._equity = self._balance + unrealized_pnl

    def get_trade_history(self) -> List[Dict]:
        """Get demo trade history"""
        return self._trade_history.copy()

    def reset_account(self, balance: float = 10000.0):
        """Reset demo account"""
        self._balance = balance
        self._equity = balance
        self._initial_balance = balance
        self._positions.clear()
        self._trade_history.clear()
        self._next_ticket = 1000
        print(f"🔄 Demo account reset to ${balance:,.2f}")

    @property
    def active_source(self) -> str:
        """Return the current data source name"""
        return f"Demo ({self._price_adapter.active_source})"
