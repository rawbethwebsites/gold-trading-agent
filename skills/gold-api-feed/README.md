# Gold API Feed & Trading Analysis Skill

Real-time precious metals and cryptocurrency price feed with comprehensive trading analysis frameworks.

## Overview

This skill combines:
- **Real-time price data** from gold-api.com (free, no API key)
- **Trading analysis** with risk management frameworks
- **Position sizing** calculations
- **Portfolio risk assessment**
- **Multi-asset correlation** analysis

## Installation

```bash
cd /Users/hitler/Projects/gold-trading-agent/skills/gold-api-feed
pip install -r requirements.txt
```

## Features

### 📊 Real-Time Prices
- **Gold (XAU/USD)**: Real-time gold spot price
- **Silver (XAG/USD)**: Silver spot price
- **Bitcoin (BTC/USD)**: Bitcoin price
- **Ethereum (ETH/USD)**: Ethereum price
- **Palladium, Platinum, Copper**: Also available

### 🛡️ Risk Management
- Position sizing based on account risk %
- Risk/reward ratio calculations
- Portfolio exposure assessment
- Trade viability evaluation

### 📈 Analysis Frameworks
- Trade setup evaluation
- Multi-asset correlation
- Market regime identification
- Decision-making support

## Quick Start

### For Claude Code

```python
from scripts.claude_code_tool import EnhancedGoldPriceTool

tool = EnhancedGoldPriceTool()

# Get prices
print(tool.get_gold_price())
print(tool.get_bitcoin_price())
print(tool.get_all_prices())

# Analyze trade
analysis = tool.analyze_trade_setup(
    asset="XAUUSD",
    entry=4640,
    stop=4620,
    target=4680,
    account=10000,
    risk=1.0
)
print(analysis)

# Calculate position size
sizing = tool.quick_position_size(
    account=10000,
    risk_percent=1.0,
    entry=4640,
    stop=4620
)
print(sizing)
```

### For OpenClaw MCP

```python
from scripts.openclaw_bridge import handle_mcp_request

request = {
    "tool": "get_price",
    "params": {"symbol": "XAU"}
}
response = handle_mcp_request(request)
```

## Available Assets

| Symbol | Asset | Type |
|--------|-------|------|
| XAU | Gold | Precious Metal |
| XAG | Silver | Precious Metal |
| BTC | Bitcoin | Cryptocurrency |
| ETH | Ethereum | Cryptocurrency |
| XPD | Palladium | Precious Metal |
| XPT | Platinum | Precious Metal |
| HG | Copper | Industrial Metal |

## API Rate Limiting

**Important**: gold-api.com requires:
- **60-second caching** between requests
- No authentication needed
- Free for commercial use
- 24/7 availability

## Trading Rules Enforced

1. **Max 2% risk per trade**
2. **Minimum 1.5:1 risk/reward ratio**
3. **Stop loss required** for all trades
4. **Max 50% portfolio exposure**
5. **5% daily loss limit**

## File Structure

```
gold-api-feed/
├── SKILL.md                    # Skill definition
├── README.md                   # This file
├── requirements.txt            # Python dependencies
└── scripts/
    ├── price_feed.py          # Core price feed
    ├── trading_analyzer.py    # Risk & position management
    ├── claude_code_tool.py    # Claude Code integration
    └── openclaw_bridge.py     # OpenClaw MCP bridge
```

## Integration with Other Skills

Combine with other skills for enhanced analysis:

- **`decision-helper`**: Evaluate multiple trade options
- **`strategy-advisor`**: Long-term market positioning
- **`data-analyst`**: Statistical analysis of returns
- **`deep-research`**: Research market fundamentals

## License

MIT License - Free for commercial and personal use.

## Data Source

- **Primary**: [gold-api.com](https://gold-api.com) - Free real-time prices
- **Fallback**: Various crypto APIs for Bitcoin/Ethereum

---

*Built for gold-trading-agent project*
