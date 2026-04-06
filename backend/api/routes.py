"""
REST API Routes for Trading Agent
Provides polling endpoints for dashboard data
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

try:
    from ..services import TradingService
except ImportError:
    from services import TradingService

router = APIRouter()

# Global trading service instance (initialized in main.py)
trading_service: Optional[TradingService] = None


class PriceResponse(BaseModel):
    timestamp: str
    symbol: str
    bid: float
    ask: float
    open: float
    high: float
    low: float
    close: float
    volume: int


class IndicatorResponse(BaseModel):
    timestamp: str
    symbol: str
    price: float
    ema_9: Optional[float]
    ema_21: Optional[float]
    sma_50: Optional[float]
    macd: Optional[float]
    macd_histogram: Optional[float]
    rsi_14: Optional[float]
    bb_upper: Optional[float]
    bb_lower: Optional[float]
    bb_percent: Optional[float]
    atr_14: Optional[float]
    trend: str
    signal_strength: float


class SignalResponse(BaseModel):
    timestamp: str
    symbol: str
    type: str
    price: float
    confidence: float
    strength: float
    reasons: List[str]
    suggested_sl: Optional[float]
    suggested_tp: Optional[float]
    indicators: Dict[str, Any]


class PositionResponse(BaseModel):
    ticket: int
    symbol: str
    type: str
    volume: float
    open_price: float
    current_price: float
    profit: float
    swap: float
    open_time: str


class AccountResponse(BaseModel):
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    open_positions: int
    account_type: str
    can_trade: bool


class StatusResponse(BaseModel):
    connected: bool
    is_trading: bool
    symbol: str
    can_trade: bool
    error: Optional[str]
    active_source: Optional[str] = "12Data"
    last_update: str


class ClosePositionRequest(BaseModel):
    ticket: int


def set_trading_service(service: TradingService):
    """Set the global trading service instance"""
    global trading_service
    trading_service = service


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get system connection and trading status"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")
    return StatusResponse(**trading_service.get_status())


@router.get("/price", response_model=Optional[PriceResponse])
async def get_price():
    """Get current price data"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    data = trading_service.get_price_data()
    if data is None:
        return None
    return PriceResponse(**data)


@router.get("/indicators", response_model=Optional[IndicatorResponse])
async def get_indicators():
    """Get current technical indicator values"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    data = trading_service.get_indicator_data()
    if data is None:
        return None
    return IndicatorResponse(**data)


@router.get("/account", response_model=Optional[AccountResponse])
async def get_account():
    """Get account information"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    data = trading_service.get_account_data()
    if data is None:
        return None
    return AccountResponse(**data)


@router.get("/positions", response_model=List[PositionResponse])
async def get_positions():
    """Get all open positions"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    positions = trading_service.get_positions_data()
    return [PositionResponse(**p) for p in positions]


@router.get("/signal", response_model=Optional[SignalResponse])
async def get_last_signal():
    """Get the most recent trading signal"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    data = trading_service.get_last_signal()
    if data is None:
        return None
    return SignalResponse(**data)


@router.post("/positions/close")
async def close_position(request: ClosePositionRequest):
    """Close a specific position by ticket"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    success = await trading_service.close_position(request.ticket)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to close position")

    return {"success": True, "ticket": request.ticket}


@router.post("/positions/close-all")
async def close_all_positions():
    """Close all open positions"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    closed_count = await trading_service.close_all_positions()
    return {"success": True, "closed": closed_count}


@router.get("/dashboard")
async def get_dashboard_data():
    """Get all data needed for dashboard in one request"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    return {
        "status": trading_service.get_status(),
        "price": trading_service.get_price_data(),
        "indicators": trading_service.get_indicator_data(),
        "account": trading_service.get_account_data(),
        "positions": trading_service.get_positions_data(),
        "signal": trading_service.get_last_signal(),
    }


@router.get("/history")
async def get_history(limit: int = 100, timeframe: str = "H1"):
    """Get historical indicator data for charts with timeframe support"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    return trading_service.get_history(limit, timeframe)


@router.get("/rates/{timeframe}")
async def get_rates_for_timeframe(timeframe: str, count: int = 100):
    """Get raw price rates for a specific timeframe (M1, M5, M15, H1, H4, D1)"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    valid_timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"]
    if timeframe not in valid_timeframes:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe. Use: {valid_timeframes}")

    rates = await trading_service.get_rates_for_timeframe(timeframe, count)
    return [
        {
            "timestamp": r.timestamp.isoformat(),
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume
        }
        for r in rates
    ]


@router.get("/config/api-status")
async def get_api_status():
    """Get current API calls enabled status"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    adapter = trading_service.adapter
    return {
        "api_calls_enabled": getattr(adapter, 'is_api_calls_enabled', True),
        "available_keys": getattr(adapter, 'available_keys', 0),
        "provider": getattr(adapter, '_provider_name', 'unknown')
    }


class ToggleApiRequest(BaseModel):
    enabled: bool


@router.post("/config/toggle-api")
async def toggle_api_calls(request: ToggleApiRequest):
    """Enable or disable API calls to save quota"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    adapter = trading_service.adapter
    if hasattr(adapter, 'enable_api_calls'):
        adapter.enable_api_calls(request.enabled)
        return {
            "success": True,
            "api_calls_enabled": adapter.is_api_calls_enabled,
            "message": f"API calls {'enabled' if request.enabled else 'disabled'}"
        }
    else:
        return {
            "success": False,
            "message": "Adapter does not support API toggle"
        }


@router.get("/trades")
async def get_trade_history():
    """Get trade history with P/L for win rate calculation"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    return trading_service.get_trade_history()
