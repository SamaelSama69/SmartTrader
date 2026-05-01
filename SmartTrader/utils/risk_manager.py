"""
Risk Manager - Enforces risk limits across all trading operations
Reads risk parameters from config and validates every trade
"""
import logging
from typing import Dict, Optional
from datetime import datetime, date
from config import (
    MAX_POSITION_PCT, MAX_DRAWDOWN_PCT, INITIAL_CAPITAL,
    TRANSACTION_COST_BPS
)

logger = logging.getLogger(__name__)


class RiskManager:
    """Centralized risk management for all trading operations"""

    def __init__(self, initial_capital: float = None):
        self.initial_capital = initial_capital or INITIAL_CAPITAL
        self.current_capital = self.initial_capital
        self.max_position_pct = MAX_POSITION_PCT
        self.max_drawdown_pct = MAX_DRAWDOWN_PCT
        self.daily_loss_limit_pct = 0.02  # 2% daily loss limit
        self.max_open_positions = 10

        self.daily_start_capital = self.current_capital
        self.open_positions = {}  # ticker -> {shares, entry_price}
        self.peak_capital = self.initial_capital
        self.trading_enabled = True

    def check_trade(self, ticker: str, shares: int, price: float) -> Dict:
        """Check if a trade is allowed under risk rules"""
        result = {'allowed': True, 'reason': '', 'adjusted_shares': shares}

        if not self.trading_enabled:
            return {'allowed': False, 'reason': 'Trading is disabled (kill-switch active)'}

        # Check max positions
        if len(self.open_positions) >= self.max_open_positions and ticker not in self.open_positions:
            return {'allowed': False, 'reason': f'Max positions ({self.max_open_positions}) reached'}

        # Check position size
        position_value = shares * price
        max_position_value = self.current_capital * self.max_position_pct
        if position_value > max_position_value:
            adjusted = int(max_position_value / price)
            result['adjusted_shares'] = max(adjusted, 0)
            result['reason'] = f'Position reduced to {adjusted} shares (max {self.max_position_pct*100:.0f}%)'

        # Check daily loss limit
        daily_pnl = self.current_capital - self.daily_start_capital
        if daily_pnl < -(self.daily_loss_limit_pct * self.initial_capital):
            return {'allowed': False, 'reason': f'Daily loss limit ({self.daily_loss_limit_pct*100:.0f}%) hit'}

        return result

    def record_trade(self, ticker: str, shares: int, price: float, side: str):
        """Record a trade for risk tracking"""
        if side.upper() == 'BUY':
            self.open_positions[ticker] = {'shares': shares, 'entry_price': price}
        elif side.upper() == 'SELL' and ticker in self.open_positions:
            del self.open_positions[ticker]

        # Update capital (simplified)
        cost = shares * price * (1 + TRANSACTION_COST_BPS / 10000)
        if side.upper() == 'BUY':
            self.current_capital -= cost
        else:
            self.current_capital += shares * price * (1 - TRANSACTION_COST_BPS / 10000)

        # Update peak
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

    def check_drawdown(self) -> Dict:
        """Check if max drawdown is exceeded"""
        if self.peak_capital == 0:
            return {'allowed': True}

        drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        if drawdown > self.max_drawdown_pct:
            self.trading_enabled = False
            return {
                'allowed': False,
                'reason': f'Max drawdown ({self.max_drawdown_pct*100:.0f}%) exceeded: {drawdown*100:.2f}%',
                'drawdown_pct': drawdown * 100
            }
        return {'allowed': True, 'drawdown_pct': drawdown * 100}

    def kill_switch(self):
        """Emergency stop - cancel all trades, disable trading"""
        self.trading_enabled = False
        logger.critical("KILL-SWITCH ACTIVATED - All trading stopped")
        return {'status': 'disabled', 'open_positions': list(self.open_positions.keys())}

    def enable_trading(self, cooldown_minutes: int = 30):
        """Re-enable trading after cooldown"""
        import time
        logger.info(f"Trading cooldown: {cooldown_minutes} minutes before re-enable")
        time.sleep(cooldown_minutes * 60)
        self.trading_enabled = True
        self.daily_start_capital = self.current_capital
        logger.info("Trading re-enabled after cooldown")
