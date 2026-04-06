"""
Gold Trading Agent - Backend (MT5 + Exness)
Local-first architecture with polling REST API
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from services.trading_service import TradingService
from api import routes
from api.routes import set_trading_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instance
trading_service: TradingService = None


def get_adapter():
    """Factory function to get the appropriate adapter"""
    provider = config.app.data_provider
    if provider == "mock":
        logger.info("Using Mock Adapter (simulated data)")
        from adapters.mock_adapter import MockAdapter
        return MockAdapter()
    elif provider == "twelve_data":
        logger.info("Using Twelve Data Adapter (real gold prices)")
        from adapters.twelve_data_adapter import TwelveDataAdapter
        return TwelveDataAdapter(api_key=config.twelve_data.api_key)
    else:
        logger.info("Using MT5 Adapter (local terminal)")
        from adapters.mt5_adapter import MT5Adapter
        return MT5Adapter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global trading_service

    logger.info("=" * 60)
    logger.info("Gold Trading Agent - Starting up")
    logger.info("=" * 60)

    # Log safety configuration
    logger.info(f"Trading enabled: {config.trading.enable_trading}")
    logger.info(f"Demo trades: {config.trading.enable_demo_trades}")
    logger.info(f"Account type: {config.account.account_type}")
    logger.info(f"Can trade: {config.can_trade}")
    logger.info(f"Data provider: {config.app.data_provider}")
    logger.info(f"Symbol: {config.mt5.symbol}")
    logger.info(f"Timeframe: {config.mt5.timeframe}")

    # Initialize adapter and trading service
    adapter = get_adapter()
    trading_service = TradingService(adapter)

    # Make trading service available to API
    set_trading_service(trading_service)

    # Start trading service (connects to MT5)
    connected = await trading_service.start()

    if not connected:
        logger.error("Failed to connect to MT5. Trading will be unavailable.")
        logger.error("Please check:")
        logger.error("  1. MT5 terminal is running")
        logger.error("  2. MetaTrader5 Python package is installed")
        logger.error("  3. MT5_TERMINAL_PATH is set correctly (if needed)")
    else:
        logger.info("Trading service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down...")
    if trading_service:
        await trading_service.stop()
    logger.info("Goodbye!")


# Create FastAPI app
app = FastAPI(
    title="Gold Trading Agent API",
    description="Local-first MT5 + Exness trading agent",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint - system info"""
    return {
        "name": "Gold Trading Agent",
        "version": "1.0.0",
        "architecture": "Local-first MT5 + Exness",
        "data_provider": config.app.data_provider,
        "symbol": config.mt5.symbol,
        "timeframe": config.mt5.timeframe,
        "trading_enabled": config.can_trade,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if trading_service is None:
        return {"status": "initializing"}

    return {
        "status": "healthy" if trading_service.state.connected else "degraded",
        "connected": trading_service.state.connected,
        "trading": trading_service.state.is_trading,
        "symbol": config.mt5.symbol
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.app.backend_host,
        port=config.app.backend_port,
        reload=False,
        log_level="info"
    )
