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
        self._last_price = 4650.0  # Realistic gold price (April 2025)
        self._failed_keys = set()  # Track keys that have hit rate limits
        self._cache_timestamp = None
        self._cache_duration = 300  # Cache for 5 minutes when API disabled
        self._provider_name = "twelve_data"
        self._active_source = "12Data"
        self._first_fetch = True  # Allow first price to set baseline

        # Gold-api.com cache (60 seconds to prevent IP blocking)
        self._gold_api_cache: Dict[str, tuple] = {}  # symbol -> (timestamp, price_data)
        self._gold_api_cache_duration = 60  # 1 minute cache as per API docs

    @property
    def active_source(self) -> str:
        """Return the current active data source name"""
        return self._active_source

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
        for attempt in range(len(self._api_keys)):
            key = self._current_key
            if not key:
                self._reset_failed_keys()
                key = self._current_key
                if not key:
                    break

            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self._base_url}/quote?symbol=XAU/USD&apikey={key}"
                    async with session.get(url, timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'close' in data:
                                print(f"✅ Connected using API key {attempt + 1}")
                                self._connected = True
                                return True
                            elif 'code' in data and data['code'] == 429:
                                # Rate limited in response body
                                print(f"⚠️  Key {attempt + 1} rate limited")
                                self._mark_key_failed(key)
                                self._rotate_key()
                            else:
                                print(f"⚠️  Key {attempt + 1} error: {data.get('message', 'Unknown')}")
                                self._mark_key_failed(key)
                                self._rotate_key()
                        elif response.status == 429:
                            # Rate limited via HTTP status
                            print(f"⚠️  Key {attempt + 1} rate limited (HTTP 429)")
                            self._mark_key_failed(key)
                            self._rotate_key()
                        else:
                            print(f"⚠️  Key {attempt + 1} HTTP error: {response.status}")
                            self._rotate_key()
            except asyncio.TimeoutError:
                print(f"⏱️  Key {attempt + 1} timeout, trying next...")
                self._rotate_key()
            except Exception as e:
                print(f"❌ Key {attempt + 1} error: {e}")
                self._rotate_key()

        # All keys failed, enable fallback mode
        print("⚠️  Twelve Data keys exhausted, using public fallback APIs")
        self._api_calls_enabled = False
        self._connected = True
        self._active_source = "Public Fallback"
        return True

    async def disconnect(self):
        """Disconnect"""
        self._connected = False

    async def _fetch_gold_api(self, symbol: str) -> Optional[PriceData]:
        """Fetch price from gold-api.com with 60-second caching to prevent IP blocking"""
        now = datetime.now()

        # Check cache first (60-second TTL as per API docs)
        if symbol in self._gold_api_cache:
            cached_time, cached_data = self._gold_api_cache[symbol]
            age_seconds = (now - cached_time).total_seconds()
            if age_seconds < self._gold_api_cache_duration:
                # Return cached data with updated timestamp
                return PriceData(
                    timestamp=now,
                    open=cached_data.open,
                    high=cached_data.high,
                    low=cached_data.low,
                    close=cached_data.close,
                    volume=cached_data.volume,
                    symbol=symbol
                )

        # Cache miss or expired - fetch from API
        symbol_map = {
            "XAUUSD": "XAU",
            "BTCUSD": "BTC",
            "XAGUSD": "XAG",
            "ETHUSD": "ETH"
        }
        api_symbol = symbol_map.get(symbol, symbol.replace("USD", ""))

        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.gold-api.com/price/{api_symbol}"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        price = float(data.get("price", 0))
                        if price > 0:
                            self._active_source = "gold-api.com"
                            price_data = PriceData(
                                timestamp=now,
                                open=price,
                                high=price,
                                low=price,
                                close=price,
                                volume=0,
                                symbol=symbol
                            )
                            # Store in cache
                            self._gold_api_cache[symbol] = (now, price_data)
                            return price_data
        except Exception as e:
            print(f"gold-api.com error: {e}")

        # Return stale cache if API fails (better than nothing)
        if symbol in self._gold_api_cache:
            _, cached_data = self._gold_api_cache[symbol]
            return PriceData(
                timestamp=now,
                open=cached_data.open,
                high=cached_data.high,
                low=cached_data.low,
                close=cached_data.close,
                volume=cached_data.volume,
                symbol=symbol
            )
        return None

    async def get_price(self, symbol: str = "XAUUSD") -> Optional[PriceData]:
        """Get current price for symbol (XAUUSD or BTCUSD)"""
        if not self.is_connected():
            return None

        # Try gold-api.com first (free, no auth, no rate limits)
        price = await self._fetch_gold_api(symbol)
        if price:
            return price

        # BTCUSD always uses fallback APIs (Twelve Data free tier doesn't include crypto)
        if symbol == "BTCUSD":
            return await self._run_bitcoin_fallback()

        # If API calls disabled, run the fallback API race instead of twelve data
        if not self._api_calls_enabled:
            return await self._run_fallback_race()

        # Try to fetch from API
        for _ in range(len(self._api_keys) or 1):
            key = self._current_key
            if not key:
                self._reset_failed_keys()
                key = self._current_key

            if not key:
                # No working keys, disable API calls
                self._api_calls_enabled = False
                return await self._run_fallback_race()

            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{self._base_url}/quote?symbol=XAU/USD&apikey={key}"
                    async with session.get(url, timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'close' in data:
                                price = float(data.get("close", 0))
                                if price > 0:
                                    self._last_price = price
                                    self._cache_timestamp = datetime.now()
                                    self._active_source = "12Data"
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

        # API failed, fall back to fallback APIs
        return await self._run_fallback_race()

    async def _run_bitcoin_fallback(self) -> Optional[PriceData]:
        """Fetch Bitcoin price from public APIs - CoinGecko is most reliable"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                # Try CoinGecko first (most reliable)
                async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        price = float(data.get("bitcoin", {}).get("usd", 0))
                        if price > 0:
                            self._active_source = "CoinGecko"
                            return PriceData(
                                timestamp=datetime.now(),
                                open=price,
                                high=price,
                                low=price,
                                close=price,
                                volume=0,
                                symbol="BTCUSD"
                            )
            except Exception:
                pass

            try:
                # Try CoinPaprika as fallback
                async with session.get("https://api.coinpaprika.com/v1/tickers/btc-bitcoin", timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        price = float(data.get("quotes", {}).get("USD", {}).get("price", 0))
                        if price > 0:
                            self._active_source = "CoinPaprika"
                            return PriceData(
                                timestamp=datetime.now(),
                                open=price,
                                high=price,
                                low=price,
                                close=price,
                                volume=0,
                                symbol="BTCUSD"
                            )
            except Exception:
                pass

            try:
                # Try Blockchain.com as last resort
                async with session.get("https://api.blockchain.com/v3/exchange/tickers/BTC-USD", timeout=10) as r:
                    if r.status == 200:
                        data = await r.json()
                        price = float(data.get("last_trade_price", 0))
                        if price > 0:
                            self._active_source = "Blockchain.com"
                            return PriceData(
                                timestamp=datetime.now(),
                                open=price,
                                high=price,
                                low=price,
                                close=price,
                                volume=0,
                                symbol="BTCUSD"
                            )
            except Exception:
                pass

        # Return cached/default
        return PriceData(
            timestamp=datetime.now(),
            open=68000.0,
            high=68000.0,
            low=68000.0,
            close=68000.0,
            volume=0,
            symbol="BTCUSD"
        )

    async def _fetch_source(self, name: str, session: aiohttp.ClientSession) -> tuple:
        """Fetch gold price from public APIs - follows HTML pattern: metals.live > goldprice.org > crypto tokens"""
        try:
            # Pattern from HTML: metals.live (primary spot reference)
            if name == "metals.live":
                async with session.get("https://api.metals.live/v1/spot", timeout=10) as r:
                    if r.status != 200:
                        return name, 0.0
                    data = await r.json()
                    # metals.live returns spot prices for gold, silver, platinum, palladium
                    if isinstance(data, list) and len(data) > 0:
                        # Find gold (XAU) entry
                        for metal in data:
                            if metal.get('symbol') == 'XAU':
                                return name, float(metal.get('price', 0))
                    return name, 0.0

            # Pattern from HTML: goldprice.org (public market check)
            elif name == "goldprice.org":
                # goldprice.org chart endpoint
                async with session.get("https://data-asg.goldprice.org/dbdata/price/ratio/XAU_USD.json", timeout=10) as r:
                    if r.status != 200:
                        return name, 0.0
                    data = await r.json()
                    if 'price' in data:
                        return name, float(data['price'])
                    return name, 0.0

            # Fallback: CoinPaprika PAXG (crypto gold token)
            elif name == "CoinPaprika_PAXG":
                async with session.get("https://api.coinpaprika.com/v1/tickers/paxg-pax-gold", timeout=10) as r:
                    if r.status != 200:
                        return name, 0.0
                    data = await r.json()
                    price = data.get("quotes", {}).get("USD", {}).get("price", 0)
                    return name, float(price)

            # Fallback: CoinPaprika XAUT (Tether Gold)
            elif name == "CoinPaprika_XAUT":
                async with session.get("https://api.coinpaprika.com/v1/tickers/xaut-tether-gold", timeout=10) as r:
                    if r.status != 200:
                        return name, 0.0
                    data = await r.json()
                    price = data.get("quotes", {}).get("USD", {}).get("price", 0)
                    return name, float(price)

            # Legacy fallbacks
            elif name == "Binance":
                async with session.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=5) as r:
                    if r.status != 200:
                        return name, 0.0
                    data = await r.json()
                    return name, float(data.get("price", 0))
            elif name == "Kraken":
                async with session.get("https://api.kraken.com/0/public/Ticker?pair=PAXGUSD", timeout=5) as r:
                    if r.status != 200:
                        return name, 0.0
                    data = await r.json()
                    return name, float(data["result"]["PAXGUSD"]["c"][0])
            elif name == "CoinGecko":
                async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd", timeout=5) as r:
                    if r.status != 200:
                        return name, 0.0
                    data = await r.json()
                    return name, float(data["pax-gold"]["usd"])
        except Exception as e:
            return name, 0.0
        return name, 0.0

    async def _run_fallback_race(self) -> PriceData:
        """
        Cascade through public APIs following HTML pattern:
        metals.live > goldprice.org > CoinPaprika > legacy sources
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            # Pattern from HTML: metals.live (primary) > goldprice.org (secondary) > crypto tokens
            sources = ["metals.live", "goldprice.org", "CoinPaprika_PAXG", "CoinPaprika_XAUT", "Binance", "Kraken", "CoinGecko"]
            tasks = [asyncio.create_task(self._fetch_source(src, session)) for src in sources]

            # Await all and filter
            results = await asyncio.gather(*tasks, return_exceptions=True)

            valid_prices = []
            for res in results:
                if isinstance(res, tuple) and res[1] > 0:
                    valid_prices.append(res)

            best_price = self._last_price

            if valid_prices:
                # Priority: metals.live > goldprice.org > crypto tokens
                # Sort by source priority
                source_priority = {
                    "metals.live": 1,      # HTML pattern: primary spot reference
                    "goldprice.org": 2,     # HTML pattern: public market check
                    "CoinPaprika_PAXG": 3,
                    "CoinPaprika_XAUT": 4,
                    "Binance": 5,
                    "Kraken": 6,
                    "CoinGecko": 7
                }
                valid_prices.sort(key=lambda x: source_priority.get(x[0], 99))

                # On first fetch, accept highest priority valid price
                if self._first_fetch:
                    source_name = valid_prices[0][0]
                    best_price = valid_prices[0][1]
                    self._first_fetch = False
                    # Map source names to match HTML pattern
                    source_display = {
                        "metals.live": "metals.live",
                        "goldprice.org": "goldprice.org",
                        "CoinPaprika_PAXG": "PAXG Token",
                        "CoinPaprika_XAUT": "XAUT Token"
                    }
                    self._active_source = source_display.get(source_name, source_name)
                    print(f"✅ Initial price from {self._active_source}: ${best_price:.2f}")
                else:
                    # Tolerance check: must not deviate > 5% from last price
                    filtered = []
                    for name, p in valid_prices:
                        if self._last_price > 0:
                            deviation = abs(p - self._last_price) / self._last_price
                            if deviation > 0.05:
                                print(f"⚠️  Ignoring outlier {name}: ${p:.2f} ({deviation*100:.1f}% deviation)")
                                continue
                        filtered.append((name, p))

                    if filtered:
                        source_name = filtered[0][0]
                        source_display = {
                            "metals.live": "metals.live",
                            "goldprice.org": "goldprice.org",
                            "CoinPaprika_PAXG": "PAXG Token",
                            "CoinPaprika_XAUT": "XAUT Token"
                        }
                        self._active_source = source_display.get(source_name, source_name)
                        best_price = filtered[0][1]
                        print(f"✅ Using {self._active_source}: ${best_price:.2f}")
                    else:
                        self._active_source = "Standby/Offline"
                        print("⚠️  All prices rejected as outliers, using cached")
            else:
                self._active_source = "Standby/Offline"
                print("⚠️  All fallback sources failed, using cached price")

            self._last_price = best_price

            return PriceData(
                timestamp=datetime.now(),
                open=best_price,
                high=best_price,
                low=best_price,
                close=best_price,
                volume=0,
                symbol="XAUUSD"
            )

    async def get_rates(self, symbol: str, timeframe: str, count: int = 100) -> List[PriceData]:
        """Get historical rates"""
        # No more mocked rates either. Return a flatlined base array representing the past just to fill charts safely 
        rates = []
        price = self._last_price

        for i in range(count, 0, -1):
            rates.append(PriceData(
                timestamp=datetime.now(),
                open=price,
                high=price,
                low=price,
                close=price,
                volume=0,
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
