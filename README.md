# Gold Trading Agent

Local-first gold (XAU/USD) trading agent for Exness + MetaTrader 5.

**NEW**: Includes AI Trading Agent with TradingAgents-inspired multi-agent analysis framework.

## What's Included

1. **Full-Stack Trading Dashboard** - Next.js frontend + FastAPI backend
2. **AI Trading Agent** - Standalone Python agent using MCP skill
3. **gold-api-feed Skill** - Real-time prices + multi-agent analysis
4. **Multi-Asset Support** - Trade Gold (XAU/USD) and Bitcoin (BTC/USD)
5. **Demo Trading Mode** - No MT5 required for testing

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

## AI Trading Agent (Standalone)

Use the trading agent without the full stack:

```bash
# Run interactive mode
python agent/trading_agent.py

# Quick commands
python agent/trading_agent.py --price XAU              # Get gold price
python agent/trading_agent.py --analyze --asset XAUUSD --price-val 4640
python agent/trading_agent.py --debate --asset XAUUSD --price-val 4640
python agent/trading_agent.py --risk --asset XAUUSD
python agent/trading_agent.py --trade --asset XAUUSD --entry 4640 --stop 4620 --target 4680
```

See [agent/README.md](agent/README.md) for full documentation.

## MCP Skill: gold-api-feed

The `skills/gold-api-feed` directory contains a reusable MCP skill for:
- Real-time precious metals & crypto prices
- Multi-agent market analysis (TradingAgents-inspired)
- Trade setup evaluation
- Bull/bear debate
- Risk assessment

Use it in your own projects:

```python
import sys
sys.path.insert(0, '/path/to/skills/gold-api-feed/scripts')
from mcp_server import handle_mcp_request

request = {
    "tool": "get_price",
    "params": {"symbol": "XAU"}
}
result = handle_mcp_request(request)
```

See [skills/gold-api-feed/SKILL.md](skills/gold-api-feed/SKILL.md) for full documentation.

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

### Trading Endpoints

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
| `GET /api/assets` | Available assets & prices |
| `POST /api/assets/switch` | Switch active asset |

### MCP AI Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/mcp/analyze-trade` | Analyze trade setup |
| `POST /api/mcp/market-analysis` | Multi-agent market analysis |
| `POST /api/mcp/run-debate` | Bull/bear debate |
| `POST /api/mcp/check-order` | Order eligibility |
| `POST /api/mcp/check-risk` | Risk assessment |

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
gold-trading-agent/
├── agent/                    # Standalone AI Trading Agent
│   ├── __init__.py
│   ├── trading_agent.py      # Main agent class
│   └── README.md             # Agent documentation
├── backend/
│   ├── adapters/             # Data source adapters
│   │   ├── __init__.py
│   │   ├── mt5_adapter.py    # MT5 local connection
│   │   ├── demo_trading_adapter.py  # Demo mode
│   │   ├── multi_asset_adapter.py   # Multi-asset mode
│   │   └── mock_adapter.py   # Simulated data
│   ├── api/                  # REST API endpoints
│   │   ├── __init__.py
│   │   └── routes.py         # All API routes + MCP
│   ├── config/               # Configuration
│   │   └── __init__.py
│   ├── services/             # Business logic
│   │   ├── __init__.py
│   │   └── trading_service.py
│   ├── main.py               # Application entry
│   └── requirements.txt      # Dependencies
├── frontend/                 # Next.js dashboard
│   └── src/
│       └── app/
│           └── page.tsx      # Main dashboard
├── skills/                   # MCP Skills
│   └── gold-api-feed/        # Trading skill
│       ├── SKILL.md          # Skill documentation
│       ├── mcp_schema.json   # MCP schema
│       ├── scripts/
│       │   ├── mcp_server.py # MCP server
│       │   ├── price_feed.py # Price feed
│       │   ├── trading_analyzer.py
│       │   ├── market_analyst.py
│       │   ├── portfolio_manager.py
│       │   └── risk_manager.py
│       └── requirements.txt
├── README.md                 # This file
└── tui.py                   # Terminal UI
```

## Demo Trading Mode (No MT5 Required)

Trade with virtual money using real market prices - no MT5 needed!

```bash
# In backend/.env
DATA_PROVIDER=demo_trading
ENABLE_TRADING=true
ENABLE_DEMO_TRADES=true
```

Features:
- Real-time prices from gold-api.com
- Virtual $10,000 starting balance
- Full trading simulation
- Works on macOS/Linux (no Windows needed)

## Multi-Asset Mode

Trade both Gold and Bitcoin:

```bash
# In backend/.env
DATA_PROVIDER=multi_asset
ASSETS=XAUUSD,BTCUSD
ENABLE_TRADING=true
```

Switch assets via the dashboard or API.

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
