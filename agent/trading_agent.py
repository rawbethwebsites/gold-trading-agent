#!/usr/bin/env python3
"""
Gold Trading Agent - Standalone AI Trading Assistant
Uses the gold-api-feed MCP skill for market analysis

Usage:
    python trading_agent.py              # Interactive mode
    python trading_agent.py --analyze    # Quick market analysis
    python trading_agent.py --debate     # Run bull/bear debate
    python trading_agent.py --risk       # Risk assessment
"""

import sys
import json
import argparse
from typing import Dict, Any, Optional

# Add skill to path
sys.path.insert(0, '/Users/hitler/Projects/gold-trading-agent/skills/gold-api-feed/scripts')

try:
    from mcp_server import handle_mcp_request
except ImportError:
    print("Error: Could not import MCP server. Make sure you're running from the repo root.")
    sys.exit(1)


class TradingAgent:
    """
    AI Trading Agent powered by gold-api-feed MCP skill

    Provides:
    - Real-time price checking
    - Multi-agent market analysis
    - Bull/bear debate
    - Trade setup evaluation
    - Risk assessment
    """

    def __init__(self):
        self.name = "Gold Trading Agent"
        self.version = "2.0.0"

    def get_price(self, symbol: str = "XAU") -> Dict[str, Any]:
        """Get current price for an asset"""
        request = {
            "tool": "get_price",
            "params": {"symbol": symbol}
        }
        return handle_mcp_request(request)

    def get_all_prices(self) -> Dict[str, Any]:
        """Get prices for all supported assets"""
        request = {
            "tool": "get_all_prices",
            "params": {}
        }
        return handle_mcp_request(request)

    def analyze_market(self, asset: str, current_price: float,
                       support: list, resistance: list,
                       rsi: Optional[float] = None,
                       trend: str = "neutral",
                       price_change_24h: float = 0.0) -> Dict[str, Any]:
        """
        Multi-agent market analysis

        Analyzes from technical, sentiment, and fundamental perspectives
        Returns consensus with confidence score
        """
        request = {
            "tool": "market_analysis",
            "params": {
                "asset": asset,
                "current_price": current_price,
                "support": support,
                "resistance": resistance,
                "rsi": rsi,
                "trend": trend,
                "price_change_24h": price_change_24h
            }
        }
        return handle_mcp_request(request)

    def run_debate(self, asset: str, current_price: float, rounds: int = 3) -> Dict[str, Any]:
        """
        Run structured bull/bear debate

        Returns verdict and round-by-round breakdown
        """
        request = {
            "tool": "run_debate",
            "params": {
                "asset": asset,
                "current_price": current_price,
                "rounds": rounds
            }
        }
        return handle_mcp_request(request)

    def analyze_trade(self, asset: str, entry: float, stop: float, target: float,
                      account: float = 10000.0, risk_percent: float = 1.0) -> Dict[str, Any]:
        """
        Analyze trade setup with position sizing

        Returns approval status, position size, risk/reward ratio
        """
        request = {
            "tool": "analyze_trade_setup",
            "params": {
                "asset": asset,
                "entry": entry,
                "stop": stop,
                "target": target,
                "account": account,
                "risk_percent": risk_percent
            }
        }
        return handle_mcp_request(request)

    def check_risk(self, assets: list, portfolio_value: float) -> Dict[str, Any]:
        """
        Comprehensive risk assessment

        Returns risk level, score, alerts, recommendations
        """
        request = {
            "tool": "check_risk",
            "params": {
                "assets": assets,
                "portfolio_value": portfolio_value
            }
        }
        return handle_mcp_request(request)

    def check_order(self, asset: str, entry: float, stop: float,
                    risk_percent: float = 1.0) -> Dict[str, Any]:
        """Check order eligibility with portfolio manager"""
        request = {
            "tool": "check_order",
            "params": {
                "asset": asset,
                "entry": entry,
                "stop": stop,
                "risk_percent": risk_percent
            }
        }
        return handle_mcp_request(request)

    def interactive_mode(self):
        """Run interactive trading assistant"""
        print(f"\n{'='*60}")
        print(f"  {self.name} v{self.version}")
        print(f"  Powered by gold-api-feed MCP Skill")
        print(f"{'='*60}\n")

        while True:
            print("\nCommands:")
            print("  price [symbol]     - Get current price (default: XAU)")
            print("  prices             - Get all asset prices")
            print("  analyze            - Market analysis")
            print("  debate             - Run bull/bear debate")
            print("  trade              - Analyze trade setup")
            print("  risk               - Risk assessment")
            print("  quit               - Exit\n")

            try:
                cmd = input("> ").strip().lower()

                if cmd == "quit":
                    break

                elif cmd.startswith("price"):
                    parts = cmd.split()
                    symbol = parts[1].upper() if len(parts) > 1 else "XAU"
                    result = self.get_price(symbol)
                    if result.get("success"):
                        print(f"\n{result['name']} ({result['symbol']}): ${result['price']:,.2f}")
                    else:
                        print(f"\nError: {result.get('error', 'Unknown error')}")

                elif cmd == "prices":
                    result = self.get_all_prices()
                    if result.get("success"):
                        print("\n--- Market Prices ---")
                        for symbol, data in result["prices"].items():
                            print(f"  {data['name']} ({symbol}): ${data['price']:,.2f}")
                    else:
                        print(f"\nError: {result.get('error', 'Unknown error')}")

                elif cmd == "analyze":
                    print("\nEnter analysis parameters:")
                    asset = input("Asset (e.g., XAUUSD): ").strip().upper() or "XAUUSD"
                    price = float(input("Current price: ").strip() or "4640")
                    support = [float(x) for x in input("Support levels (comma-separated): ").strip().split(",") if x]
                    resistance = [float(x) for x in input("Resistance levels (comma-separated): ").strip().split(",") if x]
                    rsi = float(input("RSI (optional, press enter to skip): ").strip() or 50)
                    trend = input("Trend (bullish/bearish/neutral): ").strip().lower() or "neutral"

                    print("\nAnalyzing...")
                    result = self.analyze_market(asset, price, support, resistance, rsi, trend)

                    if result.get("success"):
                        print(f"\n{'='*50}")
                        print(f"  Market Analysis: {asset}")
                        print(f"{'='*50}")
                        print(f"  Sentiment: {result['sentiment']}")
                        print(f"  Confidence: {result['confidence']*100:.0f}%")
                        print(f"  Risk Level: {result['risk_level']}")
                        print(f"  Recommendation: {result['recommendation']}")
                        print(f"\n  Bullish Points:")
                        for point in result['bullish_points'][:3]:
                            print(f"    + {point}")
                        print(f"\n  Bearish Points:")
                        for point in result['bearish_points'][:3]:
                            print(f"    - {point}")
                    else:
                        print(f"\nError: {result.get('error', 'Unknown error')}")

                elif cmd == "debate":
                    print("\nEnter debate parameters:")
                    asset = input("Asset (e.g., XAUUSD): ").strip().upper() or "XAUUSD"
                    price = float(input("Current price: ").strip() or "4640")
                    rounds = int(input("Number of rounds (1-5): ").strip() or "3")

                    print("\nRunning debate...")
                    result = self.run_debate(asset, price, rounds)

                    if result.get("success"):
                        print(f"\n{'='*50}")
                        print(f"  Debate Results: {asset}")
                        print(f"{'='*50}")
                        print(f"  Verdict: {result['verdict']}")
                        print(f"  Bull Wins: {result['bull_wins']}")
                        print(f"  Bear Wins: {result['bear_wins']}")
                        print(f"\n  Rounds:")
                        for r in result['rounds']:
                            print(f"\n    Round {r['round']}:")
                            print(f"      Bull ({r['bull_strength']:.0%}): {r['bull_argument'][:60]}...")
                            print(f"      Bear ({r['bear_strength']:.0%}): {r['bear_argument'][:60]}...")
                            print(f"      Winner: {r['winner']}")
                    else:
                        print(f"\nError: {result.get('error', 'Unknown error')}")

                elif cmd == "trade":
                    print("\nEnter trade parameters:")
                    asset = input("Asset (e.g., XAUUSD): ").strip().upper() or "XAUUSD"
                    entry = float(input("Entry price: ").strip())
                    stop = float(input("Stop loss: ").strip())
                    target = float(input("Take profit: ").strip())
                    account = float(input("Account balance (default 10000): ").strip() or "10000")
                    risk = float(input("Risk percent (default 1.0): ").strip() or "1.0")

                    print("\nAnalyzing trade...")
                    result = self.analyze_trade(asset, entry, stop, target, account, risk)

                    if result.get("success"):
                        print(f"\n{'='*50}")
                        print(f"  Trade Analysis: {asset}")
                        print(f"{'='*50}")
                        print(f"  Approved: {'YES' if result['approved'] else 'NO'}")
                        print(f"  Position Size: {result['position_size']:.2f} lots")
                        print(f"  Risk Amount: ${result['risk_amount']:.2f}")
                        print(f"  Risk/Reward: {result['risk_reward_ratio']:.2f}:1")
                        print(f"  Recommendation: {result['recommendation']}")
                        print(f"\n  Reasoning:")
                        for reason in result['reasoning'][:3]:
                            print(f"    • {reason}")
                    else:
                        print(f"\nError: {result.get('error', 'Unknown error')}")

                elif cmd == "risk":
                    print("\nEnter risk assessment parameters:")
                    assets = [x.strip().upper() for x in input("Assets (comma-separated, e.g., XAU,BTC): ").strip().split(",") if x]
                    portfolio = float(input("Portfolio value: ").strip() or "10000")

                    print("\nAssessing risk...")
                    result = self.check_risk(assets, portfolio)

                    if result.get("success"):
                        print(f"\n{'='*50}")
                        print(f"  Risk Assessment")
                        print(f"{'='*50}")
                        print(f"  Risk Level: {result['risk_level']}")
                        print(f"  Risk Score: {result['risk_score']*100:.0f}%")
                        print(f"  Alerts: {len(result['alerts'])}")
                        if result['alerts']:
                            for alert in result['alerts'][:3]:
                                print(f"    ⚠️  [{alert['level']}] {alert['message']}")
                        print(f"\n  Recommendations:")
                        for rec in result['recommendations'][:2]:
                            print(f"    • {rec}")
                    else:
                        print(f"\nError: {result.get('error', 'Unknown error')}")

                else:
                    print(f"\nUnknown command: {cmd}")

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")


def main():
    parser = argparse.ArgumentParser(description="Gold Trading Agent")
    parser.add_argument("--analyze", action="store_true", help="Run market analysis")
    parser.add_argument("--debate", action="store_true", help="Run bull/bear debate")
    parser.add_argument("--risk", action="store_true", help="Risk assessment")
    parser.add_argument("--price", type=str, help="Get price for symbol")
    parser.add_argument("--trade", action="store_true", help="Analyze trade")
    parser.add_argument("--asset", type=str, default="XAUUSD", help="Asset symbol")
    parser.add_argument("--price-val", type=float, default=4640.0, help="Current price")
    parser.add_argument("--entry", type=float, help="Entry price")
    parser.add_argument("--stop", type=float, help="Stop loss")
    parser.add_argument("--target", type=float, help="Take profit")

    args = parser.parse_args()

    agent = TradingAgent()

    if args.price:
        result = agent.get_price(args.price.upper())
        print(json.dumps(result, indent=2))

    elif args.analyze:
        result = agent.analyze_market(
            asset=args.asset,
            current_price=args.price_val,
            support=[args.price_val * 0.99, args.price_val * 0.98],
            resistance=[args.price_val * 1.01, args.price_val * 1.02],
            trend="neutral"
        )
        print(json.dumps(result, indent=2))

    elif args.debate:
        result = agent.run_debate(args.asset, args.price_val, rounds=3)
        print(json.dumps(result, indent=2))

    elif args.risk:
        result = agent.check_risk([args.asset], 10000)
        print(json.dumps(result, indent=2))

    elif args.trade:
        if not all([args.entry, args.stop, args.target]):
            print("Error: --trade requires --entry, --stop, and --target")
            sys.exit(1)
        result = agent.analyze_trade(args.asset, args.entry, args.stop, args.target)
        print(json.dumps(result, indent=2))

    else:
        # Interactive mode
        agent.interactive_mode()


if __name__ == "__main__":
    main()
