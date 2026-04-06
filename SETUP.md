# Gold Trading Agent - Setup Guide

## Step-by-Step Setup Instructions

### Step 1: Create Exness Demo Account

1. Go to [exness.com](https://exness.com)
2. Click "Sign Up" → "Create Demo Account"
3. Fill in your details
4. Save your credentials:
   - **Account Number**: Will be shown after registration
   - **Password**: You set this
   - **Server**: Usually "Exness-MT5" or similar

### Step 2: Install MetaTrader 5

**Windows**:
1. Download from [metatrader5.com](https://www.metatrader5.com/en/download)
2. Run installer
3. Note the installation path (e.g., `C:\Program Files\MetaTrader 5\`)

**macOS**:
1. Install via Wine or use Windows VM
2. Or skip to Step 5 for Mock Mode

**Linux**:
1. Use Wine: `wine mt5setup.exe`
2. Or skip to Step 5 for Mock Mode

### Step 3: Configure MT5

1. Open MetaTrader 5
2. File → Login to Trade Account
3. Enter:
   - Server: `Exness-MT5` (or your server name)
   - Login: Your Exness account number
   - Password: Your Exness password
4. Check "Save account information"
5. Click "Login"

6. Verify login:
   - Check bottom-right shows "Connected"
   - Account balance should appear
   - Market Watch should show symbols

7. Add XAUUSD to Market Watch:
   - Right-click in Market Watch
   - Select "Symbols"
   - Find "XAUUSD" (Gold)
   - Click "Show"

### Step 4: Install Python Dependencies

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For Windows + MT5: Also install MetaTrader5
pip install MetaTrader5
```

### Step 5: Configure Environment

Edit `backend/.env`:

```bash
# ============================================
# REQUIRED: Your Exness Demo Credentials
# ============================================
ACCOUNT_NUMBER=12345678          # Your demo account number
ACCOUNT_PASSWORD=your_password   # Your demo password
ACCOUNT_SERVER=Exness-MT5        # Your server name

# ============================================
# OPTIONAL: MT5 Terminal Path (Windows only)
# ============================================
# Leave empty for auto-detection on Windows
# For macOS/Linux: Use mock mode (see below)
# MT5_TERMINAL_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# ============================================
# TRADING SETTINGS
# ============================================
# To enable trading, BOTH must be true:
ENABLE_TRADING=false
ENABLE_DEMO_TRADES=false

MAX_OPEN_POSITIONS=1
DEFAULT_LOT_SIZE=0.01
MAX_DAILY_LOSS_PERCENT=2.0

# ============================================
# SYMBOL & TIMEFRAME
# ============================================
SYMBOL=XAUUSD
TIMEFRAME=H1

# ============================================
# DATA PROVIDER
# ============================================
# mt5 = Local MT5 terminal
# mock = Simulated data (for testing)
DATA_PROVIDER=mt5

# For macOS/Linux without MT5, use:
# DATA_PROVIDER=mock
```

### Step 6: Test MT5 Connection

```bash
cd backend
python -c "
import asyncio
from adapters.mt5_adapter import MT5Adapter

async def test():
    adapter = MT5Adapter()
    connected = await adapter.connect()
    print(f'Connected: {connected}')
    if connected:
        price = await adapter.get_price('XAUUSD')
        print(f'Price: {price}')
        account = await adapter.get_account_info()
        print(f'Account: {account}')
    await adapter.disconnect()

asyncio.run(test())
"
```

Expected output:
```
Connected: True
Price: PriceData(timestamp=..., close=2650.50, ...)
Account: AccountInfo(balance=10000.0, ...)
```

### Step 7: Start Backend

```bash
cd backend
python main.py
```

You should see:
```
Gold Trading Agent - Starting up
Trading enabled: False
Demo trades: False
Account type: demo
Can trade: False
Data provider: mt5
Symbol: XAUUSD
Trading service started successfully
```

Test the API:
```bash
curl http://localhost:8000/api/status
curl http://localhost:8000/api/price
curl http://localhost:8000/api/account
```

### Step 8: Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3005` in your browser.

### Step 9: Enable Trading (When Ready)

**ONLY proceed when you're confident with the system!**

1. Stop the backend (Ctrl+C)
2. Edit `.env`:
   ```
   ENABLE_TRADING=true
   ENABLE_DEMO_TRADES=true
   ```
3. Restart backend
4. Verify in logs: `Can trade: True`
5. Verify API: `curl http://localhost:8000/api/account` shows `"can_trade": true`

### Step 10: Verify Safety

Before trusting the system with real money:

1. **Demo Check**: `curl http://localhost:8000/api/account` should show `"account_type": "demo"`
2. **Position Limit**: System should reject orders beyond `MAX_OPEN_POSITIONS`
3. **Daily Loss**: System stops after `MAX_DAILY_LOSS_PERCENT` loss
4. **Manual Override**: You can always close positions in MT5 terminal

## Troubleshooting

### "MT5 initialization failed"

**Problem**: Can't connect to MT5

**Solutions**:
1. Is MT5 running? Check taskbar/system tray
2. Try setting explicit path in `.env`:
   ```
   MT5_TERMINAL_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
   ```
3. Check Windows Event Viewer for MT5 errors

### "MT5 not logged in"

**Problem**: MT5 connected but not logged into Exness

**Solutions**:
1. Open MT5 and check bottom-right corner
2. Should show "Connected" with your account number
3. If not, File → Login to Trade Account

### "MetaTrader5 package not installed"

**Problem**: MetaTrader5 Python package missing

**Solutions**:
1. `pip install MetaTrader5`
2. **Note**: Only works on Windows!
3. On macOS/Linux, use Mock Mode for testing

### "Risk check failed: Trading not enabled"

**Problem**: Trading safety guards active

**Solutions**:
1. Check `ENABLE_TRADING=true` in `.env`
2. Check `ENABLE_DEMO_TRADES=true` in `.env`
3. Restart backend after changing `.env`

### "Risk check failed: Account type is 'real'"

**Problem**: Safety feature - code refuses to trade on real accounts

**Solutions**:
1. Login to Exness **demo** account in MT5
2. Verify account type with: `curl http://localhost:8000/api/account`
3. Should show `"account_type": "demo"`

## Mock Mode (macOS/Linux/Testing)

If you can't install MT5, use Mock Mode:

```bash
# In backend/.env
DATA_PROVIDER=mock
ENABLE_TRADING=true
```

This simulates:
- Random gold price movements
- Fake account balance ($10,000 demo)
- Simulated positions
- All trading logic works, but no real money

## Next Steps

1. **Understand the Signals**: Read `backend/core/signal_engine.py` to understand signal logic
2. **Adjust Parameters**: Modify indicators in `backend/core/indicator_engine.py`
3. **Add Telegram**: Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env` for alerts
4. **Backtest**: Use historical data to test strategies (not yet implemented)
5. **Paper Trade**: Run for a week on demo to verify performance

## Safety Checklist

Before any trading:
- [ ] Running on demo account only
- [ ] `ENABLE_TRADING=true` in `.env`
- [ ] `ENABLE_DEMO_TRADES=true` in `.env`
- [ ] `MAX_OPEN_POSITIONS` set conservatively
- [ ] `DEFAULT_LOT_SIZE` set to minimum
- [ ] `MAX_DAILY_LOSS_PERCENT` set to 2% or less
- [ ] Verified account type is "demo" in dashboard
- [ ] Tested position close functionality
- [ ] Know how to stop the system (Ctrl+C on backend)

## Support

If you encounter issues:
1. Check backend logs for error messages
2. Test MT5 connection with Step 6 command
3. Verify `.env` settings
4. Check this SETUP.md troubleshooting section
