# Gold Trading Agent

Local-first gold (XAU/USD) trading agent for Exness + MetaTrader 5.

## Architecture

```
┌─────────────────┐     REST API      ┌──────────────────┐
│   Next.js       │ ←──────────────→ │   FastAPI        │
│   Dashboard     │    Polling        │   Backend        │
└─────────────────┘                   └────────┬─────────┘
                                               │
                                               │ MetaTrader5
                                               │ Python Package
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

## Features

- **Local-First**: MT5 terminal runs on your laptop, direct integration
- **Technical Analysis**: RSI, MACD, EMA 9/21, SMA 50, Bollinger Bands, ATR
- **Signal Engine**: Confluence-based BUY/SELL signals (2+ indicators agree)
- **Trading Safety**: Demo-only enforcement, position limits, daily loss guards
- **REST API**: Polling-based endpoints for dashboard
- **Telegram Alerts**: Optional notifications for signals and trades

## Quick Start

### Prerequisites

1. **Exness Demo Account**: Create one at [exness.com](https://exness.com)
2. **MetaTrader 5**: Download from [metatrader5.com](https://metatrader5.com)
3. **Python 3.9+**: Required for backend

### 1. Setup MT5

1. Install MT5 on your laptop
2. Open MT5 and login to Exness demo account
3. Make sure `XAUUSD` is visible in Market Watch
4. Keep MT5 running while using the agent

### 2. Configure Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Edit `.env` file:

```bash
# Required: Your Exness demo credentials
ACCOUNT_NUMBER=your_account_number
ACCOUNT_PASSWORD=your_password
ACCOUNT_SERVER=Exness-MT5

# Optional: MT5 terminal path (auto-detected on Windows)
# MT5_TERMINAL_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# Safety: Enable demo trading
ENABLE_TRADING=true
ENABLE_DEMO_TRADES=true

# Symbol and timeframe
SYMBOL=XAUUSD
TIMEFRAME=H1
```

### 3. Run Backend

```bash
cd backend
python main.py
```

Backend starts on `http://localhost:8000`

### 4. Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend starts on `http://localhost:3005`

### 5. Access Dashboard

Open `http://localhost:3005` to see:
- Real-time price from MT5
- Technical indicators
- Trading signals
- Account balance & positions
- Risk status

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/status` | System connection status |
| `GET /api/price` | Current price data |
| `GET /api/indicators` | Technical indicator values |
| `GET /api/account` | Account info & balance |
| `GET /api/positions` | Open positions |
| `GET /api/signal` | Last trading signal |
| `GET /api/dashboard` | All data in one request |
| `POST /api/positions/close` | Close position by ticket |
| `POST /api/positions/close-all` | Close all positions |

## Trading Safety

**Default Configuration (Safe)**:
- `ENABLE_TRADING=false` - Trading disabled by default
- `ENABLE_DEMO_TRADES=false` - Demo trades disabled by default
- `MAX_OPEN_POSITIONS=1` - Max 1 position at a time
- `DEFAULT_LOT_SIZE=0.01` - Minimum micro-lot
- `MAX_DAILY_LOSS_PERCENT=2.0` - Stop trading after 2% daily loss

**To enable trading**:
1. Must be logged into Exness **demo** account in MT5
2. Set `ENABLE_TRADING=true` and `ENABLE_DEMO_TRADES=true`
3. Verify account info shows `"account_type": "demo"`

## Technical Indicators

| Indicator | Period | Purpose |
|-----------|--------|---------|
| EMA 9 | Fast trend | Short-term momentum |
| EMA 21 | Medium trend | Trend direction |
| SMA 50 | Slow trend | Major trend filter |
| RSI | 14 | Momentum (overbought/oversold) |
| MACD | 12/26/9 | Trend momentum crossover |
| Bollinger Bands | 20 | Volatility & mean reversion |
| ATR | 14 | Volatility for SL/TP calculation |

## Signal Logic

**BUY Signal** (2+ indicators agree):
- RSI < 30 (oversold)
- MACD bullish crossover
- Price at lower Bollinger Band
- EMA alignment bullish

**SELL Signal** (2+ indicators agree):
- RSI > 70 (overbought)
- MACD bearish crossover
- Price at upper Bollinger Band
- EMA alignment bearish

**Risk Management**:
- SL = 2x ATR from entry
- TP = 4x ATR from entry (1:2 risk/reward)

## Project Structure

```
backend/
├── adapters/           # Data source adapters
│   ├── __init__.py     # Adapter interfaces
│   ├── mt5_adapter.py  # MT5 local connection
│   └── mock_adapter.py # Simulated data (testing)
├── api/                # REST API endpoints
│   ├── __init__.py
│   └── routes.py       # All API routes
├── config/             # Configuration
│   └── __init__.py
├── core/               # Trading logic
│   ├── __init__.py
│   ├── indicator_engine.py  # Technical analysis
│   ├── signal_engine.py     # Signal generation
│   └── risk_manager.py      # Risk management
├── services/           # Business logic
│   ├── __init__.py
│   ├── trading_service.py       # Main orchestrator
│   └── notification_service.py  # Telegram alerts
├── main.py             # Application entry
└── requirements.txt    # Dependencies
```

## Mock Mode (No MT5)

To test without MT5:

```bash
# In .env
DATA_PROVIDER=mock
ENABLE_TRADING=true
```

This generates simulated price data for testing the system.

## Troubleshooting

### MT5 Connection Issues

1. **"MT5 initialization failed"**
   - Ensure MT5 terminal is running
   - Check MT5_TERMINAL_PATH in .env
   - On Windows: Use full path to `terminal64.exe`

2. **"MT5 not logged in"**
   - Login to Exness demo account in MT5
   - Check "Keep me logged in" in MT5

3. **"MetaTrader5 package not installed"**
   - MetaTrader5 package only works on Windows
   - Use `DATA_PROVIDER=mock` on macOS/Linux for testing

### API Issues

1. **"Trading service not initialized"**
   - Wait for backend to fully start
   - Check backend logs for errors

2. **"Risk check failed"**
   - Check `ENABLE_TRADING` and `ENABLE_DEMO_TRADES` are true
   - Verify account type is "demo"

## Security & Safety

- **Demo-only enforcement**: Code checks `account_type == "demo"`
- **Position limits**: Configurable max open positions
- **Daily loss guard**: Trading stops after max loss
- **Margin check**: Won't trade if margin level < 100%
- **No real trading**: Requires explicit opt-in for demo trades

## Future: MetaApi Cloud

The adapter pattern allows adding MetaApi cloud support:

```python
# In .env
DATA_PROVIDER=metaapi
METAAPI_ACCOUNT_ID=your_account_id
METAAPI_TOKEN=your_token
```

This enables running without local MT5 (not yet implemented).

## License

MIT - For educational purposes only. Not financial advice.
