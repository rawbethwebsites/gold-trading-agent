"""
Goldrix Package

Provides AI-powered trading analysis using the gold-api-feed MCP skill.

Usage:
    from agent.trading_agent import TradingAgent

    agent = TradingAgent()

    # Get current price
    price = agent.get_price("XAU")

    # Analyze market
    analysis = agent.analyze_market(
        asset="XAUUSD",
        current_price=4640.0,
        support=[4620, 4600],
        resistance=[4660, 4680]
    )

    # Run debate
    debate = agent.run_debate("XAUUSD", 4640.0, rounds=3)

    # Check risk
    risk = agent.check_risk(["XAUUSD"], portfolio_value=10000)
"""

from .trading_agent import TradingAgent

__version__ = "2.1.0"
__all__ = ["TradingAgent"]
