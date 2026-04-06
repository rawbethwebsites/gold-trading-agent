"""
Risk Manager
Position sizing, risk controls, and trade safety
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime, timedelta

from ..config import config
from ..adapters import AccountInfo, Position


@dataclass
class RiskCheck:
    """Result of a risk check"""
    allowed: bool
    reason: str
    adjusted_lot_size: Optional[float] = None


class RiskManager:
    """
    Manages trading risk and position sizing.
    Enforces daily loss limits, position limits, and account safety.
    """

    def __init__(self):
        self._daily_pnl_start: Optional[float] = None
        self._daily_pnl_current: float = 0.0
        self._last_reset: Optional[datetime] = None
        self._trade_history: list = []

        # Risk parameters from config
        self.max_daily_loss_pct = config.trading.max_daily_loss_percent
        self.max_positions = config.trading.max_open_positions
        self.default_lot_size = config.trading.default_lot_size

    def can_trade(
        self,
        account: Optional[AccountInfo],
        current_positions: list,
        new_signal_type: str
    ) -> RiskCheck:
        """
        Check if a new trade can be placed.
        Returns RiskCheck with allowed status and reason.
        """
        # Safety check: trading must be enabled
        if not config.can_trade:
            return RiskCheck(
                allowed=False,
                reason="Trading not enabled. Set ENABLE_TRADING=true and ENABLE_DEMO_TRADES=true"
            )

        # Check account exists
        if account is None:
            return RiskCheck(allowed=False, reason="No account connection")

        # Check account type is demo
        if account.account_type != "demo":
            return RiskCheck(
                allowed=False,
                reason=f"Safety block: Account type is '{account.account_type}', only 'demo' allowed"
            )

        # Check position limit
        if len(current_positions) >= self.max_positions:
            return RiskCheck(
                allowed=False,
                reason=f"Max positions reached: {len(current_positions)}/{self.max_positions}"
            )

        # Check for existing position in same direction
        for pos in current_positions:
            if pos.type == new_signal_type:
                return RiskCheck(
                    allowed=False,
                    reason=f"Already have {new_signal_type} position open"
                )

        # Check daily loss limit
        daily_loss_check = self._check_daily_loss_limit(account)
        if not daily_loss_check.allowed:
            return daily_loss_check

        # Check margin level
        if account.margin_level < 100:
            return RiskCheck(
                allowed=False,
                reason=f"Margin level too low: {account.margin_level:.1f}%"
            )

        # Calculate adjusted lot size
        adjusted_lot = self._calculate_position_size(account)

        return RiskCheck(
            allowed=True,
            reason="Risk check passed",
            adjusted_lot_size=adjusted_lot
        )

    def _check_daily_loss_limit(self, account: AccountInfo) -> RiskCheck:
        """Check if daily loss limit has been exceeded"""
        self._reset_daily_if_needed()

        if self._daily_pnl_start is None:
            self._daily_pnl_start = account.equity
            self._last_reset = datetime.now()

        # Calculate current daily P&L
        daily_pnl_pct = ((account.equity - self._daily_pnl_start) / self._daily_pnl_start) * 100

        if daily_pnl_pct <= -self.max_daily_loss_pct:
            return RiskCheck(
                allowed=False,
                reason=f"Daily loss limit reached: {daily_pnl_pct:.1f}% (limit: -{self.max_daily_loss_pct}%)"
            )

        return RiskCheck(allowed=True, reason="Daily loss check passed")

    def _calculate_position_size(self, account: AccountInfo) -> float:
        """
        Calculate position size based on account equity and risk parameters.
        Conservative sizing for gold (XAU/USD) volatility.
        """
        # Base lot size from config
        lot_size = self.default_lot_size

        # Adjust based on equity (micro-lots for small accounts)
        if account.equity < 1000:
            lot_size = 0.01  # Minimum micro-lot
        elif account.equity < 5000:
            lot_size = 0.02
        elif account.equity < 10000:
            lot_size = 0.05
        else:
            lot_size = 0.1

        # Cap at config default if set lower
        return min(lot_size, self.default_lot_size)

    def _reset_daily_if_needed(self):
        """Reset daily stats if it's a new day"""
        if self._last_reset is None:
            return

        now = datetime.now()
        if now.date() != self._last_reset.date():
            self._daily_pnl_start = None
            self._daily_pnl_current = 0.0
            self._trade_history.clear()

    def update_after_trade(self, position: Position):
        """Update risk tracking after a trade is placed"""
        self._trade_history.append({
            "time": datetime.now(),
            "ticket": position.ticket,
            "type": position.type,
            "volume": position.volume
        })

    def get_daily_stats(self) -> dict:
        """Get current daily trading statistics"""
        self._reset_daily_if_needed()

        return {
            "trades_today": len(self._trade_history),
            "daily_pnl": self._daily_pnl_current,
            "last_reset": self._last_reset.isoformat() if self._last_reset else None,
            "max_daily_loss_pct": self.max_daily_loss_pct,
        }

    def calculate_risk_reward(
        self,
        entry: float,
        stop_loss: float,
        take_profit: float,
        position_type: str
    ) -> Tuple[float, float]:
        """
        Calculate risk/reward ratio and dollar risk.
        Returns (risk_reward_ratio, dollar_risk)
        """
        if position_type == "buy":
            risk = entry - stop_loss
            reward = take_profit - entry
        else:
            risk = stop_loss - entry
            reward = entry - take_profit

        if risk <= 0:
            return 0.0, 0.0

        risk_reward = reward / risk
        # Approximate dollar risk (1 lot ≈ $10 per pip for gold, rough estimate)
        dollar_risk = risk * 10  # Simplified calculation

        return risk_reward, dollar_risk
