"""
Tests for RiskManager
"""
import pytest
from utils.risk_manager import RiskManager

class TestRiskManager:
    def setup_method(self):
        self.rm = RiskManager(initial_capital=100000)

    def test_initialization(self):
        assert self.rm.initial_capital == 100000
        assert self.rm.trading_enabled == True
        assert len(self.rm.open_positions) == 0

    def test_check_trade_allowed(self):
        # 100 shares * $150 = $15,000 > 10% of $100k ($10k), so adjusted down
        result = self.rm.check_trade("AAPL", 100, 150.0)
        assert result['allowed'] == True
        # Max position is 10% of 100k = 10k, 10k / 150 = 66.66 → 66 shares
        assert result['adjusted_shares'] == 66
        assert "Position reduced" in result['reason']

    def test_check_trade_max_positions(self):
        # Fill up positions
        for i in range(10):
            self.rm.open_positions[f"TICKER{i}"] = {'shares': 10, 'entry_price': 100}

        result = self.rm.check_trade("AAPL", 10, 100.0)
        assert result['allowed'] == False
        assert "Max positions" in result['reason']

    def test_check_trade_position_size(self):
        # Try to buy more than max position allows
        result = self.rm.check_trade("AAPL", 10000, 100.0)  # $1M position on $100K capital
        assert result['adjusted_shares'] < 10000  # Should be reduced

    def test_kill_switch(self):
        assert self.rm.trading_enabled == True
        result = self.rm.kill_switch()
        assert self.rm.trading_enabled == False
        assert result['status'] == 'disabled'

    def test_check_trade_after_killswitch(self):
        self.rm.kill_switch()
        result = self.rm.check_trade("AAPL", 10, 100.0)
        assert result['allowed'] == False
        assert "disabled" in result['reason'].lower()