"""
Notification Service
Sends alerts via Telegram for signals, trades, and system events
"""

import logging
from typing import Optional
import aiohttp

try:
    from ..config import config
except ImportError:
    from config import config

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Send notifications via Telegram Bot API.
    Falls back to logging if Telegram not configured.
    """

    def __init__(self):
        self.bot_token = config.app.telegram_bot_token
        self.chat_id = config.app.telegram_chat_id
        self._enabled = bool(self.bot_token and self.chat_id)

        if self._enabled:
            logger.info("Telegram notifications enabled")
        else:
            logger.info("Telegram notifications disabled (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)")

    async def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Send a plain text message"""
        if not self._enabled:
            logger.info(f"[TELEGRAM] {message}")
            return True

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return True
                    else:
                        logger.warning(f"Telegram API error: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def send_signal_alert(self, signal_data: dict) -> bool:
        """Send a formatted signal alert"""
        signal_type = signal_data.get("type", "UNKNOWN")
        symbol = signal_data.get("symbol", "XAUUSD")
        price = signal_data.get("price", 0)
        confidence = signal_data.get("confidence", 0)
        reasons = signal_data.get("reasons", [])

        emoji = "🟢" if signal_type == "buy" else "🔴" if signal_type == "sell" else "⚪"

        message = f"""{emoji} **TRADING SIGNAL: {signal_type.upper()}**

**Symbol:** {symbol}
**Price:** {price:.2f}
**Confidence:** {confidence:.0%}
**Strength:** {signal_data.get('strength', 0):.2f}

**Reasons:**
{chr(10).join(f"• {r}" for r in reasons)}

**SL:** {signal_data.get('suggested_sl', 'N/A')}
**TP:** {signal_data.get('suggested_tp', 'N/A')}
"""

        return await self.send_message(message)

    async def send_trade_alert(self, trade_data: dict, action: str = "OPENED") -> bool:
        """Send a trade execution alert"""
        emoji = "✅" if action == "OPENED" else "🚫" if action == "CLOSED" else "📊"

        message = f"""{emoji} **TRADE {action}**

**Ticket:** {trade_data.get('ticket', 'N/A')}
**Symbol:** {trade_data.get('symbol', 'XAUUSD')}
**Type:** {trade_data.get('type', 'UNKNOWN').upper()}
**Volume:** {trade_data.get('volume', 0)}
**Price:** {trade_data.get('price', 0):.2f}
"""

        if trade_data.get('profit') is not None:
            profit = trade_data['profit']
            profit_emoji = "🟢" if profit >= 0 else "🔴"
            message += f"\n**P/L:** {profit_emoji} {profit:+.2f}"

        return await self.send_message(message)

    async def send_status_alert(self, status_data: dict) -> bool:
        """Send periodic status update"""
        message = f"""📊 **SYSTEM STATUS**

**Connected:** {'✅ Yes' if status_data.get('connected') else '❌ No'}
**Trading:** {'✅ Enabled' if status_data.get('is_trading') else '⏸️ Disabled'}
**Symbol:** {status_data.get('symbol', 'N/A')}
"""

        account = status_data.get('account')
        if account:
            message += f"""
**Account:**
• Balance: ${account.get('balance', 0):.2f}
• Equity: ${account.get('equity', 0):.2f}
• Open Positions: {account.get('open_positions', 0)}
"""

        return await self.send_message(message)

    async def send_error_alert(self, error_message: str) -> bool:
        """Send an error alert"""
        message = f"""⚠️ **ERROR ALERT**

{error_message}

Please check the system.
"""
        return await self.send_message(message)
