# Goldrix - Project Summary

## What Has Been Built

A local-first gold (XAU/USD) trading dashboard and agent that connects to MetaTrader 5 on your laptop for Exness demo account trading.

## Architecture Overview

```
┌─────────────────┐     REST API      ┌──────────────────┐
│   Next.js       │ ←──────────────→ │   FastAPI        │
│   Dashboard     │    Polling (5s)   │   Backend        │
└─────────────────┘                   └────────┬─────────┘
                                               │
                                               │ MetaTrader5 Python
                                               │ Package (Windows)
                                               │
                                        ┌──────▼──────┐
                                        │   MT5       │
                                        │  Terminal   │
                                        │  (Local)    │
                                        └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │   Exness    │
                                        │   (Demo)    │
                                        └─────────────┘
```

## Key Components

### Backend (`/backend`)

#### 1. Adapters (`/backend/adapters/`)
- **`__init__.py`**: Abstract base classes (DataAdapter, TradingAdapter) + data structures (PriceData, AccountInfo, Position)
- **`mt5_adapter.py`**: Full MT5 implementation using official MetaTrader5 Python package
  - Connects to local MT5 terminal
  - Gets prices, rates, account info, positions
  - Places/closes/modifies orders
  - Safety guards (demo-only, position limits)
- **`mock_adapter.py`**: Simulated data for testing without MT5

#### 2. Core (`/backend/core/`)
- **`indicator_engine.py`**: Technical analysis calculations
  - EMA 9/21, SMA 50
  - MACD (12/26/9)
  - RSI 14
  - Bollinger Bands (20, 2σ)
  - ATR 14
  - Signal strength calculation
- **`signal_engine.py`**: Signal generation
  - Confluence algorithm (2+ indicators agree)
  - BUY/SELL/HOLD signals
  - Confidence scoring
  - SL/TP suggestions (2x/4x ATR)
- **`risk_manager.py`**: Risk management
  - Demo-only enforcement
  - Position limits
  - Daily loss guards
  - Margin checks

#### 3. Services (`/backend/services/`)
- **`trading_service.py`**: Main orchestrator
  - Connects adapter + engines + risk manager
  - Polling loop (5 second interval)
  - Data aggregation for API
- **`notification_service.py`**: Telegram alerts (optional)

#### 4. API (`/backend/api/`)
- **`routes.py`**: REST endpoints
  - `GET /api/status` - System status
  - `GET /api/price` - Current price
  - `GET /api/indicators` - Technical indicators
  - `GET /api/account` - Account info
  - `GET /api/positions` - Open positions
  - `GET /api/signal` - Last signal
  - `GET /api/dashboard` - All data combined
  - `POST /api/positions/close` - Close position
  - `POST /api/positions/close-all` - Close all

#### 5. Configuration (`/backend/config/`)
- **`__init__.py`**: Environment-based config
  - Trading safety settings
  - MT5 connection settings
  - Account credentials
  - Feature flags

### Frontend (`/frontend`)

- **`src/app/page.tsx`**: Goldrix dashboard
  - Polling-based data fetching (5s)
  - MT5 connection status
  - Account info display (balance, equity, margin)
  - Open positions with close buttons
  - Trading safety status
  - Technical indicator charts
  - Signal display with confidence

## Safety Features

### Demo-Only Enforcement
```python
@property
def can_trade(self) -> bool:
    return self.trading.enable_trading and self.account.account_type == "demo"
```

### Position Limits
- `MAX_OPEN_POSITIONS=1` (default)
- System rejects orders beyond limit

### Daily Loss Guard
- `MAX_DAILY_LOSS_PERCENT=2.0` (default)
- Trading stops after 2% daily loss

### Other Guards
- Margin level check (>100% required)
- Same-direction position check
- Trading enabled flag check

## Signal Algorithm

### BUY Signal (2+ indicators agree):
1. RSI < 30 (oversold)
2. MACD bullish crossover
3. Price at lower Bollinger Band
4. EMA alignment bullish

### SELL Signal (2+ indicators agree):
1. RSI > 70 (overbought)
2. MACD bearish crossover
3. Price at upper Bollinger Band
4. EMA alignment bearish

### Risk Management:
- SL = Entry - (2 × ATR)
- TP = Entry + (4 × ATR)
- 1:2 risk/reward ratio

## Configuration File (`.env`)

```bash
# Trading Safety (MUST BE SET)
ENABLE_TRADING=false
ENABLE_DEMO_TRADES=false
MAX_OPEN_POSITIONS=1
DEFAULT_LOT_SIZE=0.01
MAX_DAILY_LOSS_PERCENT=2.0

# MT5 Connection
MT5_TERMINAL_PATH=  # Optional (auto-detected)
SYMBOL=XAUUSD
TIMEFRAME=H1

# Exness Account (YOUR CREDENTIALS)
ACCOUNT_TYPE=demo
ACCOUNT_NUMBER=your_number
ACCOUNT_PASSWORD=your_password
ACCOUNT_SERVER=Exness-MT5

# Data Provider
DATA_PROVIDER=mt5  # or 'mock' for testing
```

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Connection status |
| `/api/price` | GET | Current price |
| `/api/indicators` | GET | All indicators |
| `/api/account` | GET | Account info |
| `/api/positions` | GET | Open positions |
| `/api/signal` | GET | Last signal |
| `/api/dashboard` | GET | All data combined |
| `/api/positions/close` | POST | Close by ticket |
| `/api/positions/close-all` | POST | Close all |

## How to Start

### Option 1: Using start.sh
```bash
./start.sh
```

### Option 2: Manual
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Access
- Dashboard: http://localhost:3005
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Next Steps (For User)

### To Test (Mock Mode):
1. Set `DATA_PROVIDER=mock` in `.env`
2. Set `ENABLE_TRADING=true` and `ENABLE_DEMO_TRADES=true`
3. Run `./start.sh`
4. Open http://localhost:3005

### To Trade (Real):
1. Create Exness demo account
2. Install MT5 on Windows
3. Login to Exness demo in MT5
4. Set credentials in `.env`
5. Set `ENABLE_TRADING=true` and `ENABLE_DEMO_TRADES=true`
6. Run `./start.sh`
7. Verify account type shows "demo"
8. Test with small positions first

## Files Created/Modified

### New Backend Files:
- `backend/adapters/__init__.py`
- `backend/adapters/mt5_adapter.py`
- `backend/adapters/mock_adapter.py`
- `backend/core/__init__.py`
- `backend/core/indicator_engine.py`
- `backend/core/signal_engine.py`
- `backend/core/risk_manager.py`
- `backend/services/__init__.py`
- `backend/services/trading_service.py`
- `backend/services/notification_service.py`
- `backend/api/__init__.py`
- `backend/api/routes.py`
- `backend/config/__init__.py`
- `backend/.env`
- `backend/requirements.txt` (updated)

### Modified Files:
- `backend/main.py` - Complete rewrite for MT5 + REST API
- `frontend/src/app/page.tsx` - Updated for polling + MT5 data
- `README.md` - Complete rewrite

### Documentation:
- `README.md` - Project overview
- `SETUP.md` - Step-by-step setup guide
- `PROJECT_SUMMARY.md` - This file

## Technical Decisions

1. **Local-First**: MT5 on laptop vs MetaApi cloud
   - Rationale: Free, direct control, no API costs
   - Trade-off: Must keep laptop on

2. **Polling vs WebSockets**: REST API with 5s polling
   - Rationale: Simpler, works behind firewalls
   - Trade-off: Slightly higher latency

3. **Python for Backend**: FastAPI + MetaTrader5 package
   - Rationale: Official MT5 Python package
   - Trade-off: Windows-only for live trading

4. **Demo-Only Enforcement**: Hard-coded safety check
   - Rationale: Prevents accidental live trading
   - Trade-off: Must modify code for real accounts

5. **Adapter Pattern**: Abstract base classes
   - Rationale: Easy to add MetaApi later
   - Trade-off: Slightly more code

## Known Limitations

1. **Windows Only**: MetaTrader5 Python package requires Windows
   - Workaround: Use Mock Mode on macOS/Linux

2. **Polling Latency**: 5 second refresh vs real-time
   - Rationale: Sufficient for H1 timeframe
   - Can be lowered if needed

3. **Single Symbol**: Currently only XAUUSD
   - Can be expanded by changing SYMBOL env var

4. **Manual Configuration**: MT5 path, credentials in .env
   - Trade-off for local-first architecture
