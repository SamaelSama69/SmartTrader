"""
Unit tests for utils/sentiment_analyzer.py
Uses pytest framework
"""

import pytest
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.sentiment_analyzer import SentimentAnalyzer, TechnicalSentimentAnalyzer
from utils.validators import validate_ticker


class TestSentimentAnalyzer:
    """Tests for SentimentAnalyzer class"""

    @pytest.fixture
    def analyzer(self):
        """Create a SentimentAnalyzer instance"""
        return SentimentAnalyzer()

    def test_init(self, analyzer):
        """Test initialization"""
        assert analyzer is not None
        assert analyzer.vader is not None

    def test_compute_text_sentiment_positive(self, analyzer):
        """Test sentiment analysis on positive text"""
        text = "This stock is amazing! Great earnings, very bullish!"
        result = analyzer.compute_text_sentiment(text)
        assert isinstance(result, dict)
        assert 'compound' in result
        assert result['compound'] > 0  # Should be positive

    def test_compute_text_sentiment_negative(self, analyzer):
        """Test sentiment analysis on negative text"""
        text = "Terrible earnings, stock crashing, bearish market!"
        result = analyzer.compute_text_sentiment(text)
        assert isinstance(result, dict)
        assert 'compound' in result
        assert result['compound'] < 0  # Should be negative

    def test_compute_text_sentiment_empty(self, analyzer):
        """Test sentiment analysis on empty text"""
        result = analyzer.compute_text_sentiment('')
        assert isinstance(result, dict)
        assert result['compound'] == 0.0

    def test_compute_text_sentiment_none(self, analyzer):
        """Test sentiment analysis on None input"""
        result = analyzer.compute_text_sentiment(None)
        assert isinstance(result, dict)
        assert result['compound'] == 0.0

    def test_get_aggregate_sentiment(self, analyzer):
        """Test aggregate sentiment (may use cached results)"""
        result = analyzer.get_aggregate_sentiment('AAPL')
        assert isinstance(result, dict)
        assert 'ticker' in result
        assert 'aggregate_sentiment' in result
        assert 'sources' in result

    def test_label_sentiment_positive(self, analyzer):
        """Test sentiment labeling for positive scores"""
        label = analyzer._label_sentiment(0.5)
        assert label == "Positive"

    def test_label_sentiment_negative(self, analyzer):
        """Test sentiment labeling for negative scores"""
        label = analyzer._label_sentiment(-0.5)
        assert label == "Negative"

    def test_label_sentiment_neutral(self, analyzer):
        """Test sentiment labeling for neutral scores"""
        label = analyzer._label_sentiment(0.0)
        assert label == "Neutral"

    def test_label_sentiment_boundary_positive(self, analyzer):
        """Test sentiment labeling at boundary (0.05)"""
        label = analyzer._label_sentiment(0.05)
        assert label == "Positive"

    def test_label_sentiment_boundary_negative(self, analyzer):
        """Test sentiment labeling at boundary (-0.05)"""
        label = analyzer._label_sentiment(-0.05)
        assert label == "Negative"


class TestTechnicalSentimentAnalyzer:
    """Tests for TechnicalSentimentAnalyzer class"""

    @pytest.fixture
    def analyzer(self):
        """Create a TechnicalSentimentAnalyzer instance"""
        return TechnicalSentimentAnalyzer()

    def test_init(self, analyzer):
        """Test initialization"""
        assert analyzer is not None

    def test_get_alpha_vantage_indicators_no_key(self):
        """Test getting indicators without API key"""
        analyzer = TechnicalSentimentAnalyzer()
        analyzer.alpha_vantage_key = ""  # Ensure no key
        result = analyzer.get_alpha_vantage_indicators('AAPL')
        assert isinstance(result, dict)
        assert len(result) == 0  # Should return empty dict

    def test_get_finnhub_technical_indicators_no_key(self):
        """Test getting indicators without API key"""
        analyzer = TechnicalSentimentAnalyzer()
        analyzer.finnhub_key = ""  # Ensure no key
        result = analyzer.get_finnhub_technical_indicators('AAPL')
        assert isinstance(result, dict)
        assert len(result) == 0  # Should return empty dict

    def test_get_tradingview_ideas_sentiment(self, analyzer):
        """Test getting TradingView ideas sentiment"""
        # This may fail due to network, so we just check the return type
        result = analyzer.get_tradingview_ideas_sentiment('AAPL')
        assert isinstance(result, dict)
        assert 'has_ideas' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
