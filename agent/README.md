# Goldrix

AI-powered trading assistant using the gold-api-feed MCP skill. Provides real-time market analysis, trade evaluation, and risk assessment.

## Quick Start

```bash
# Run interactive mode
python agent/trading_agent.py

# Get current gold price
python agent/trading_agent.py --price XAU

# Get bitcoin price
python agent/trading_agent.py --price BTC

# Analyze market
python agent/trading_agent.py --analyze --asset XAUUSD --price-val 4640

# Run bull/bear debate
python agent/trading_agent.py --debate --asset XAUUSD --price-val 4640

# Check risk
python agent/trading_agent.py --risk --asset XAUUSD

# Analyze trade setup
python agent/trading_agent.py --trade --asset XAUUSD --entry 4640 --stop 4620 --target 4680
```

## Interactive Mode Commands

```
> price XAU          # Get gold price
> prices             # Get all asset prices
> analyze            # Multi-agent market analysis
> debate             # Run bull/bear debate
> trade              # Analyze trade setup
> risk               # Risk assessment
> quit               # Exit
```

## Python API

```python
from agent.trading_agent import TradingAgent

agent = TradingAgent()

# Get price
result = agent.get_price("XAU")
print(f"Gold: ${result['price']}")

# Market analysis
analysis = agent.analyze_market(
    asset="XAUUSD",
    current_price=4640.0,
    support=[4620, 4600],
    resistance=[4660, 4680],
    rsi=55,
    trend="neutral"
)
print(f"Sentiment: {analysis['sentiment']}")
print(f"Confidence: {analysis['confidence']*100}%")

# Run debate
debate = agent.run_debate("XAUUSD", 4640.0, rounds=3)
print(f"Verdict: {debate['verdict']}")

# Analyze trade
trade = agent.analyze_trade(
    asset="XAUUSD",
    entry=4640,
    stop=4620,
    target=4680,
    account=10000,
    risk_percent=1.0
)
print(f"Approved: {trade['approved']}")
print(f"Position Size: {trade['position_size']} lots")

# Risk assessment
risk = agent.check_risk(
    assets=["XAUUSD", "BTCUSD"],
    portfolio_value=10000
)
print(f"Risk Level: {risk['risk_level']}")
```

## Supported Assets

- XAU (Gold)
- XAG (Silver)
- BTC (Bitcoin)
- ETH (Ethereum)
- XPD (Palladium)
- XPT (Platinum)
- HG (Copper)

## Features

- **Multi-Agent Analysis**: Technical, sentiment, and fundamental perspectives
- **Bull/Bear Debate**: Structured debate with configurable rounds
- **Trade Analysis**: Position sizing, risk/reward calculation
- **Risk Assessment**: VaR, volatility, drawdown monitoring
- **Portfolio Management**: Order validation, exposure tracking

## Data Source

Real-time prices from gold-api.com (free, no API key required)
