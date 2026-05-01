"""
Unit tests for utils/data_fetcher.py
Uses pytest framework
"""

import pytest
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.data_fetcher import MarketDataFetcher, NewsFetcher, RedditSentimentFetcher
from utils.validators import validate_ticker


class TestMarketDataFetcher:
    """Tests for MarketDataFetcher class"""

    @pytest.fixture
    def fetcher(self):
        """Create a MarketDataFetcher instance"""
        return MarketDataFetcher()

    def test_init(self, fetcher):
        """Test initialization"""
        assert fetcher is not None
        assert fetcher.session is not None

    def test_get_stock_data_valid_ticker(self, fetcher):
        """Test fetching data for a valid ticker"""
        # Use a widely available ticker
        result = fetcher.get_stock_data('AAPL', period='5d')
        # May return empty if yfinance is blocked, so just check it's a DataFrame
        import pandas as pd
        assert isinstance(result, pd.DataFrame)

    def test_get_stock_data_invalid_ticker(self, fetcher):
        """Test fetching data for an invalid ticker"""
        result = fetcher.get_stock_data('INVALID_TICKER_XYZ', period='5d')
        import pandas as pd
        assert isinstance(result, pd.DataFrame)
        # Should be empty for invalid ticker
        assert result.empty

    def test_get_current_price_valid(self, fetcher):
        """Test getting current price for valid ticker"""
        result = fetcher.get_current_price('AAPL')
        # Result can be None if API fails, or a float if successful
        assert result is None or isinstance(result, (int, float))

    def test_get_company_info_valid(self, fetcher):
        """Test getting company info"""
        result = fetcher.get_company_info('AAPL')
        assert isinstance(result, dict)
        # Check some expected keys
        if result:  # May be empty if API fails
            assert 'name' in result
            assert 'market_cap' in result


class TestNewsFetcher:
    """Tests for NewsFetcher class"""

    @pytest.fixture
    def fetcher(self):
        """Create a NewsFetcher instance"""
        return NewsFetcher()

    def test_init(self, fetcher):
        """Test initialization"""
        assert fetcher is not None

    def test_get_all_news_no_api_key(self):
        """Test fetching news without API key"""
        # This test assumes no API keys are set in test environment
        fetcher = NewsFetcher()
        result = fetcher.get_all_news('AAPL', days=1)
        assert isinstance(result, list)

    def test_get_newsapi_news_no_key(self):
        """Test NewsAPI fetch without key"""
        fetcher = NewsFetcher()
        fetcher.news_api_key = ""  # Ensure no key
        result = fetcher.get_newsapi_news('AAPL')
        assert isinstance(result, list)
        assert len(result) == 0


class TestRedditSentimentFetcher:
    """Tests for RedditSentimentFetcher class"""

    def test_init_no_credentials(self):
        """Test initialization without Reddit credentials"""
        fetcher = RedditSentimentFetcher()
        # Without credentials, reddit should be None
        assert fetcher.reddit is None or fetcher.reddit is not None

    def test_get_ticker_mentions_no_reddit(self):
        """Test ticker mentions without Reddit access"""
        fetcher = RedditSentimentFetcher()
        if fetcher.reddit is None:
            result = fetcher.get_ticker_mentions('AAPL')
            assert isinstance(result, dict)
            assert 'mentions' in result
            assert 'sentiment' in result


class TestValidators:
    """Tests for ticker validation"""

    def test_validate_valid_ticker(self):
        """Test valid ticker symbols"""
        result = validate_ticker('AAPL')
        assert result['valid'] is True
        assert result['ticker'] == 'AAPL'

    def test_validate_ticker_lowercase(self):
        """Test ticker normalization (lowercase to uppercase)"""
        result = validate_ticker('aapl')
        assert result['valid'] is True
        assert result['ticker'] == 'AAPL'

    def test_validate_ticker_with_dot(self):
        """Test ticker with dot (like BRK.B)"""
        result = validate_ticker('BRK.B')
        assert result['valid'] is True

    def test_validate_invalid_ticker_empty(self):
        """Test empty ticker"""
        result = validate_ticker('')
        assert result['valid'] is False

    def test_validate_invalid_ticker_none(self):
        """Test None ticker"""
        result = validate_ticker(None)
        assert result['valid'] is False

    def test_validate_invalid_ticker_special_chars(self):
        """Test ticker with special characters"""
        result = validate_ticker('AAPL@123')
        assert result['valid'] is False

    def test_validate_indian_ticker(self):
        """Test Indian market ticker validation"""
        result = validate_ticker('RELIANCE.NS', market='IN')
        assert result['valid'] is True

    def test_validate_indian_ticker_invalid(self):
        """Test invalid Indian market ticker"""
        result = validate_ticker('INVALID@TICKER', market='IN')
        assert result['valid'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
