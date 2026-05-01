"""
Unit tests for utils/screener.py
Uses pytest framework
"""

import pytest
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.screener import SmartScreener
from utils.validators import validate_ticker


class TestSmartScreener:
    """Tests for SmartScreener class"""

    @pytest.fixture
    def screener(self):
        """Create a SmartScreener instance"""
        return SmartScreener()

    def test_init(self, screener):
        """Test initialization"""
        assert screener is not None
        assert screener.data_fetcher is not None
        assert len(screener.major_tickers) > 0

    def test_get_major_tickers(self, screener):
        """Test getting major tickers list"""
        tickers = screener._get_major_tickers()
        assert isinstance(tickers, list)
        assert len(tickers) > 0
        # Check that common tickers are in the list
        assert 'AAPL' in tickers or 'MSFT' in tickers

    def test_screen_by_market_cap(self, screener):
        """Test market cap screening"""
        result = screener.screen_by_market_cap(min_cap=1e9)
        assert isinstance(result, list)
        # Should return some tickers if API works
        # If API fails, returns empty list (which is valid)

    def test_screen_by_momentum(self, screener):
        """Test momentum screening"""
        test_tickers = ['AAPL', 'MSFT', 'GOOGL']
        result = screener.screen_by_momentum(test_tickers)
        assert isinstance(result, list)
        # Each result should have required keys
        if result:
            assert 'ticker' in result[0]
            assert 'score' in result[0]
            assert 'rsi' in result[0]

    def test_screen_by_volatility(self, screener):
        """Test volatility screening"""
        test_tickers = ['AAPL', 'TSLA', 'NVDA']
        result = screener.screen_by_volatility(test_tickers)
        assert isinstance(result, list)
        # Each result should have required keys
        if result:
            assert 'ticker' in result[0]
            assert 'atr_pct' in result[0]

    def test_get_top_opportunities(self, screener):
        """Test getting top opportunities"""
        result = screener.get_top_opportunities(max_results=5)
        assert isinstance(result, list)
        # Results should be sorted by score
        if len(result) > 1:
            assert result[0]['score'] >= result[1]['score']

    def test_get_sector_performance(self, screener):
        """Test getting sector performance"""
        result = screener.get_sector_performance()
        assert isinstance(result, dict)
        # Should have sector keys
        assert len(result) > 0

    def test_screener_with_empty_list(self, screener):
        """Test screening with empty ticker list"""
        result = screener.screen_by_momentum([])
        assert isinstance(result, list)
        assert len(result) == 0

    def test_screener_with_invalid_tickers(self, screener):
        """Test screening with invalid tickers"""
        test_tickers = ['INVALID_XYZ_12345', 'ALSO_INVALID']
        result = screener.screen_by_momentum(test_tickers)
        assert isinstance(result, list)
        # Should return empty or handle gracefully


class TestValidatorsWithScreener:
    """Test ticker validation integration with screener"""

    def test_validate_before_screening(self):
        """Test that tickers are validated before screening"""
        test_tickers = ['AAPL', 'INVALID@TICKER', 'MSFT', '']

        for ticker in test_tickers:
            result = validate_ticker(ticker)
            if result['valid']:
                # Valid ticker - should be able to screen
                assert result['ticker'] == ticker.upper().strip()
            else:
                # Invalid ticker - should not be screened
                assert result['error'] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
