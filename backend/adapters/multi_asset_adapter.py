"""
Multi-Asset Trading Adapter
Supports Gold (XAU/USD) and Bitcoin (BTC/USD) with unified interface
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from . import TradingAdapter, PriceData, AccountInfo, Position
from .demo_trading_adapter import DemoTradingAdapter


@dataclass
class AssetConfig:
    """Configuration for a tradeable asset"""
    symbol: str
    display_name: str
    pip_value: float  # Value per pip/lot
    margin_per_lot: float
    decimals: int  # Price display decimals
    min_lot: float = 0.01
    max_lot: float = 10.0


ASSETS = {
    "XAUUSD": AssetConfig(
        symbol="XAUUSD",
        display_name="Gold",
        pip_value=1.0,  # $1 per pip for 1 lot
        margin_per_lot=1000.0,
        decimals=2
    ),
    "BTCUSD": AssetConfig(
        symbol="BTCUSD",
        display_name="Bitcoin",
        pip_value=1.0,  # $1 per $1 move
        margin_per_lot=5000.0,  # Higher margin for crypto
        decimals=2
    ),
}


class MultiAssetAdapter(TradingAdapter):
    """
    Multi-asset trading adapter supporting Gold and Bitcoin.
    Uses DemoTradingAdapter underneath but extends for multiple assets.
    """

    def __init__(self, initial_balance: float = 10000.0, assets: List[str] = None, api_keys: List[str] = None):
        self._assets = assets or ["XAUUSD", "BTCUSD"]
        self._asset_configs = {s: ASSETS[s] for s in self._assets if s in ASSETS}
        self._api_keys = api_keys or []

        # Create underlying adapters for each asset
        self._adapters: Dict[str, DemoTradingAdapter] = {}
        self._active_asset = "XAUUSD"  # Default active

        for asset in self._assets:
            self._adapters[asset] = DemoTradingAdapter(
                initial_balance=initial_balance,
                symbol=asset,
                api_keys=self._api_keys
            )

        self._connected = False
        self._active_source = "Multi-Asset"

    @property
    def active_asset(self) -> str:
        return self._active_asset

    @property
    def available_assets(self) -> List[str]:
        return list(self._assets)

    def set_active_asset(self, asset: str):
        """Switch active trading asset"""
        if asset in self._assets:
            self._active_asset = asset
            self._active_source = f"Demo ({asset})"
            print(f"🔄 Switched to {ASSETS[asset].display_name} ({asset})")

    async def connect(self) -> bool:
        """Connect all asset adapters"""
        print("🔗 Connecting Multi-Asset Trading Mode...")
        print(f"   Assets: {', '.join(self._assets)}")

        for asset, adapter in self._adapters.items():
            connected = await adapter.connect()
            if not connected:
                print(f"⚠️  Warning: Could not connect {asset}")

        self._connected = True
        print("✅ Multi-Asset Mode connected!")
        return True

    async def disconnect(self):
        """Disconnect all adapters"""
        for adapter in self._adapters.values():
            await adapter.disconnect()
        self._connected = False

    async def get_price(self, symbol: str = None) -> Optional[PriceData]:
        """Get price for specific or active asset"""
        target = symbol or self._active_asset
        if target in self._adapters:
            return await self._adapters[target].get_price(target)
        return None

    async def get_rates(self, symbol: str, timeframe: str, count: int = 100) -> List[PriceData]:
        """Get historical rates"""
        if symbol in self._adapters:
            return await self._adapters[symbol].get_rates(symbol, timeframe, count)
        return []

    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get combined account info across all assets"""
        # Aggregate all positions
        total_balance = 0
        total_equity = 0
        total_margin = 0
        total_positions = 0

        for adapter in self._adapters.values():
            acc = await adapter.get_account_info()
            if acc:
                total_balance += acc.balance
                total_equity += acc.equity
                total_margin += acc.margin
                total_positions += acc.open_positions

        return AccountInfo(
            balance=total_balance / len(self._adapters),  # Average balance
            equity=total_equity,
            margin=total_margin,
            free_margin=total_equity - total_margin,
            margin_level=(total_equity / total_margin * 100) if total_margin > 0 else 100.0,
            open_positions=total_positions,
            account_type="demo"
        )

    async def get_positions(self) -> List[Position]:
        """Get all positions across assets"""
        all_positions = []
        for asset, adapter in self._adapters.items():
            positions = await adapter.get_positions()
            all_positions.extend(positions)
        return all_positions

    async def get_symbols(self) -> List[str]:
        """Available symbols"""
        return list(self._assets)

    async def place_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Place order on specific asset"""
        if symbol in self._adapters:
            return await self._adapters[symbol].place_order(
                symbol, order_type, volume, price, sl, tp
            )
        return None

    async def close_position(self, ticket: int, symbol: str = None) -> bool:
        """Close position - need symbol to identify which adapter"""
        # Try to find which adapter has this ticket
        for asset, adapter in self._adapters.items():
            if symbol and asset != symbol:
                continue
            positions = await adapter.get_positions()
            if any(p.ticket == ticket for p in positions):
                return await adapter.close_position(ticket)
        return False

    async def modify_position(self, ticket: int, sl: Optional[float] = None,
                             tp: Optional[float] = None, symbol: str = None) -> bool:
        """Modify position SL/TP"""
        for asset, adapter in self._adapters.items():
            if symbol and asset != symbol:
                continue
            positions = await adapter.get_positions()
            if any(p.ticket == ticket for p in positions):
                return await adapter.modify_position(ticket, sl, tp)
        return False

    def is_connected(self) -> bool:
        return self._connected

    @property
    def active_source(self) -> str:
        return f"Multi-Asset ({self._active_asset})"

    # Asset-specific helpers
    def get_asset_config(self, symbol: str) -> Optional[AssetConfig]:
        return self._asset_configs.get(symbol)

    async def get_asset_prices(self) -> Dict[str, float]:
        """Get current prices for all assets"""
        prices = {}
        for symbol, adapter in self._adapters.items():
            price_data = await adapter.get_price(symbol)
            if price_data:
                prices[symbol] = price_data.close
        return prices
