"""
REST API Routes for Trading Agent
Provides polling endpoints for dashboard data
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
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


@router.get("/assets")
async def get_assets():
    """Get available assets and their current prices"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    adapter = trading_service.adapter

    # Check if multi-asset adapter
    if hasattr(adapter, 'get_asset_prices'):
        prices = await adapter.get_asset_prices()
        return {
            "assets": list(prices.keys()),
            "prices": prices,
            "active": getattr(adapter, 'active_asset', 'XAUUSD')
        }

    # Single asset fallback
    price_data = await adapter.get_price()
    return {
        "assets": ["XAUUSD"],
        "prices": {"XAUUSD": price_data.close} if price_data else {},
        "active": "XAUUSD"
    }


@router.post("/assets/switch")
async def switch_asset(symbol: str):
    """Switch active trading asset (for multi-asset mode)"""
    if trading_service is None:
        raise HTTPException(status_code=503, detail="Trading service not initialized")

    adapter = trading_service.adapter

    if hasattr(adapter, 'set_active_asset'):
        adapter.set_active_asset(symbol)
        # Immediately fetch price for new asset
        price_data = await adapter.get_price(symbol)
        return {
            "success": True,
            "active_asset": symbol,
            "price": {
                "symbol": price_data.symbol if price_data else symbol,
                "close": price_data.close if price_data else None,
                "bid": price_data.close if price_data else None,
                "ask": price_data.close if price_data else None
            } if price_data else None
        }

    return {"success": False, "message": "Multi-asset mode not enabled"}


# MCP Request Models - using Dict for flexibility
class TradeAnalysisRequest(BaseModel):
    asset: str
    entry: float
    stop: float
    target: float
    account: float = 10000.0
    risk_percent: float = 1.0


class MarketAnalysisRequest(BaseModel):
    asset: str
    current_price: float
    support: List[float]
    resistance: List[float]
    rsi: Optional[float] = None
    trend: str = "neutral"
    price_change_24h: float = 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "asset": "XAUUSD",
                "current_price": 4640.0,
                "support": [4620, 4600],
                "resistance": [4660, 4680],
                "rsi": 55,
                "trend": "neutral",
                "price_change_24h": 0.45
            }
        }


class DebateRequest(BaseModel):
    asset: str
    current_price: float
    rounds: int = 3


class OrderCheckRequest(BaseModel):
    asset: str
    entry: float
    stop: float
    risk_percent: float = 1.0


class RiskCheckRequest(BaseModel):
    assets: List[str]
    portfolio_value: float


# Import MCP skill tools
import sys
sys.path.insert(0, '/Users/hitler/Projects/gold-trading-agent/skills/gold-api-feed/scripts')
from mcp_server import handle_mcp_request


@router.post("/mcp/analyze-trade")
async def mcp_analyze_trade(request: Dict[str, Any] = Body(...)):
    """MCP tool: Analyze trade setup"""
    mcp_request = {
        "tool": "analyze_trade_setup",
        "params": request
    }
    return handle_mcp_request(mcp_request)


@router.post("/mcp/market-analysis")
async def mcp_market_analysis(request: Dict[str, Any] = Body(...)):
    """MCP tool: Multi-agent market analysis"""
    mcp_request = {
        "tool": "market_analysis",
        "params": request
    }
    return handle_mcp_request(mcp_request)


@router.post("/mcp/run-debate")
async def mcp_run_debate(request: Dict[str, Any] = Body(...)):
    """MCP tool: Run bull/bear debate"""
    mcp_request = {
        "tool": "run_debate",
        "params": request
    }
    return handle_mcp_request(mcp_request)


@router.post("/mcp/check-order")
async def mcp_check_order(request: Dict[str, Any] = Body(...)):
    """MCP tool: Check order eligibility"""
    mcp_request = {
        "tool": "check_order",
        "params": request
    }
    return handle_mcp_request(mcp_request)


@router.post("/mcp/check-risk")
async def mcp_check_risk(request: Dict[str, Any] = Body(...)):
    """MCP tool: Risk assessment"""
    mcp_request = {
        "tool": "check_risk",
        "params": request
    }
    return handle_mcp_request(mcp_request)
