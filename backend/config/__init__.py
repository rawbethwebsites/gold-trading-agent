"""
Configuration module for Exness + MT5 Trading Agent
Loads settings from environment with safe defaults
"""

import os
from dataclasses import dataclass
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class TradingConfig:
    """Trading safety configuration"""
    enable_trading: bool = False
    enable_demo_trades: bool = False
    max_open_positions: int = 1
    default_lot_size: float = 0.01
    max_daily_loss_percent: float = 2.0


@dataclass
class MT5Config:
    """MetaTrader 5 connection settings"""
    terminal_path: Optional[str] = None
    symbol: str = "XAUUSD"
    timeframe: str = "H1"


@dataclass
class AccountConfig:
    """Exness account settings"""
    account_type: str = "demo"
    account_number: Optional[int] = None
    account_password: Optional[str] = None
    server: str = "Exness-MT5"
    initial_balance: float = 10000.0  # Starting balance for demo trading mode


@dataclass
class TwelveDataConfig:
    """Twelve Data API settings for real gold prices"""
    api_keys: list = None  # List of API keys for rotation
    current_key_index: int = 0
    enabled: bool = False
    api_calls_enabled: bool = True  # Master switch to turn API calls on/off

    def __post_init__(self):
        if self.api_keys is None:
            self.api_keys = []

    @property
    def current_key(self) -> Optional[str]:
        """Get current API key"""
        if self.api_keys and 0 <= self.current_key_index < len(self.api_keys):
            return self.api_keys[self.current_key_index]
        return None

    def rotate_key(self) -> Optional[str]:
        """Rotate to next API key"""
        if not self.api_keys:
            return None
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return self.current_key

    @property
    def has_available_keys(self) -> bool:
        """Check if there are any API keys available"""
        return len(self.api_keys) > 0


@dataclass
class MetaApiConfig:
    """Optional MetaApi cloud adapter settings"""
    account_id: Optional[str] = None
    token: Optional[str] = None
    region: str = "va"
    enabled: bool = False


@dataclass
class AppConfig:
    """Application settings"""
    data_provider: str = "mt5"  # mt5, mock, twelve_data
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    polling_interval: int = 5
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None


class Config:
    """Main configuration class"""

    def __init__(self):
        self.trading = TradingConfig(
            enable_trading=self._get_bool("ENABLE_TRADING", False),
            enable_demo_trades=self._get_bool("ENABLE_DEMO_TRADES", False),
            max_open_positions=self._get_int("MAX_OPEN_POSITIONS", 1),
            default_lot_size=self._get_float("DEFAULT_LOT_SIZE", 0.01),
            max_daily_loss_percent=self._get_float("MAX_DAILY_LOSS_PERCENT", 2.0),
        )

        self.mt5 = MT5Config(
            terminal_path=os.getenv("MT5_TERMINAL_PATH"),
            symbol=os.getenv("SYMBOL", "XAUUSD"),
            timeframe=os.getenv("TIMEFRAME", "H1"),
        )

        self.account = AccountConfig(
            account_type=os.getenv("ACCOUNT_TYPE", "demo"),
            account_number=self._get_int("ACCOUNT_NUMBER", None),
            account_password=os.getenv("ACCOUNT_PASSWORD"),
            server=os.getenv("ACCOUNT_SERVER", "Exness-MT5"),
            initial_balance=self._get_float("INITIAL_BALANCE", 10000.0),
        )

        self.metaapi = MetaApiConfig(
            account_id=os.getenv("METAAPI_ACCOUNT_ID"),
            token=os.getenv("METAAPI_TOKEN"),
            region=os.getenv("METAAPI_REGION", "va"),
            enabled=bool(os.getenv("METAAPI_ACCOUNT_ID") and os.getenv("METAAPI_TOKEN")),
        )

        # Parse multiple API keys (comma-separated)
        api_keys_str = os.getenv("TWELVE_DATA_API_KEYS", "")
        api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]

        self.twelve_data = TwelveDataConfig(
            api_keys=api_keys,
            enabled=os.getenv("DATA_PROVIDER") == "twelve_data",
            api_calls_enabled=self._get_bool("TWELVE_DATA_API_CALLS_ENABLED", True),
        )

        self.app = AppConfig(
            data_provider=os.getenv("DATA_PROVIDER", "mt5"),
            backend_host=os.getenv("BACKEND_HOST", "0.0.0.0"),
            backend_port=self._get_int("BACKEND_PORT", 8000),
            polling_interval=self._get_int("POLLING_INTERVAL", 5),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        )

    def _get_bool(self, key: str, default: bool) -> bool:
        """Parse boolean from environment"""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def _get_int(self, key: str, default: Optional[int]) -> Optional[int]:
        """Parse integer from environment"""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def _get_float(self, key: str, default: float) -> float:
        """Parse float from environment"""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default

    @property
    def can_trade(self) -> bool:
        """Check if trading is enabled and safe"""
        return self.trading.enable_trading and self.account.account_type == "demo"

    @property
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode"""
        return self.app.data_provider == "mock"


# Global config instance
config = Config()
