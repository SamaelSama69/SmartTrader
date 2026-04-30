"""
Sentiment Analyzer - Uses free pre-computed sources + local analysis
Offloads computation to free APIs when possible
"""

import requests
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from typing import Dict, List, Optional
from datetime import datetime
import time

from config import *


class SentimentAnalyzer:
    """
    Multi-source sentiment analysis
    Uses pre-computed sentiment from APIs when available (saves compute)
    """

    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        self.finnhub_key = FINNHUB_API_KEY
        self.news_api_key = NEWS_API_KEY

    def get_finnhub_sentiment(self, ticker: str) -> Dict:
        """
        Get pre-computed sentiment from Finnhub (free, already computed server-side)
        This offloads compute to their servers
        """
        if not self.finnhub_key:
            return {'sentiment_score': 0.0, 'news_score': 0.0, 'social_score': 0.0}

        try:
            # Finnhub provides pre-computed sentiment
            url = f"https://finnhub.io/api/v1/stock/social-sentiment"
            params = {'symbol': ticker, 'token': self.finnhub_key}
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Reddit sentiment (pre-computed by Finnhub)
                reddit_score = 0.0
                if 'reddit' in data and data['reddit']:
                    scores = [d.get('score', 0) for d in data['reddit']]
                    reddit_score = sum(scores) / len(scores) if scores else 0.0

                # Twitter sentiment (pre-computed by Finnhub)
                twitter_score = 0.0
                if 'twitter' in data and data['twitter']:
                    scores = [d.get('score', 0) for d in data['twitter']]
                    twitter_score = sum(scores) / len(scores) if scores else 0.0

                return {
                    'sentiment_score': (reddit_score + twitter_score) / 2,
                    'reddit_sentiment': reddit_score,
                    'twitter_sentiment': twitter_score,
                    'source': 'finnhub_precomputed'
                }
        except Exception as e:
            print(f"Finnhub sentiment error: {e}")

        return {'sentiment_score': 0.0, 'reddit_sentiment': 0.0, 'twitter_sentiment': 0.0}

    def get_newsapi_sentiment(self, ticker: str, days: int = 7) -> Dict:
        """
        Get sentiment from News API articles
        Uses VADER locally but on a small subset (API limits to 100/day)
        """
        if not self.news_api_key:
            return {'sentiment': 0.0, 'article_count': 0}

        try:
            from_date = (datetime.now() - pd.Timedelta(days=days)).strftime('%Y-%m-%d')
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': ticker,
                'from': from_date,
                'language': 'en',
                'sortBy': 'publishedAt',
                'apiKey': self.news_api_key,
                'pageSize': 25  # Limit to save API calls
            }
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                articles = response.json().get('articles', [])
                if not articles:
                    return {'sentiment': 0.0, 'article_count': 0}

                # Compute sentiment locally (lightweight with VADER)
                sentiments = []
                for article in articles:
                    text = (article.get('title', '') + ' ' + article.get('description', ''))
                    if text.strip():
                        score = self.vader.polarity_scores(text)['compound']
                        sentiments.append(score)

                avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
                return {
                    'sentiment': avg_sentiment,
                    'article_count': len(articles),
                    'source': 'newsapi_vader'
                }
        except Exception as e:
            print(f"NewsAPI sentiment error: {e}")

        return {'sentiment': 0.0, 'article_count': 0}

    def compute_text_sentiment(self, text: str) -> Dict:
        """Lightweight local sentiment (VADER + TextBlob)"""
        if not text or not text.strip():
            return {'compound': 0.0, 'polarity': 0.0, 'subjectivity': 0.0}

        vader_scores = self.vader.polarity_scores(text)
        blob = TextBlob(text)

        return {
            'compound': vader_scores['compound'],
            'pos': vader_scores['pos'],
            'neg': vader_scores['neg'],
            'neu': vader_scores['neu'],
            'polarity': blob.sentiment.polarity,
            'subjectivity': blob.sentiment.subjectivity
        }

    def get_aggregate_sentiment(self, ticker: str) -> Dict:
        """
        Aggregate sentiment from multiple pre-computed sources
        Minimizes local compute by using API-provided sentiment
        """
        results = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }

        # 1. Finnhub pre-computed sentiment (server-side compute)
        finnhub_sent = self.get_finnhub_sentiment(ticker)
        results['sources']['finnhub'] = finnhub_sent

        # 2. NewsAPI with local VADER (lightweight)
        news_sent = self.get_newsapi_sentiment(ticker)
        results['sources']['newsapi'] = news_sent

        # 3. Compute weighted average
        total_weight = 0
        weighted_sum = 0.0

        if finnhub_sent.get('sentiment_score', 0) != 0:
            weighted_sum += finnhub_sent['sentiment_score'] * 2.0  # Weight Finnhub more
            total_weight += 2.0

        if news_sent.get('sentiment', 0) != 0:
            weighted_sum += news_sent['sentiment'] * 1.5
            total_weight += 1.5

        results['aggregate_sentiment'] = weighted_sum / total_weight if total_weight > 0 else 0.0
        results['sentiment_label'] = self._label_sentiment(results['aggregate_sentiment'])

        return results

    def _label_sentiment(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score >= 0.05:
            return "Positive"
        elif score <= -0.05:
            return "Negative"
        else:
            return "Neutral"


class TechnicalSentimentAnalyzer:
    """
    Uses free APIs that provide pre-computed technical indicators
    Reduces local compute significantly
    """

    def __init__(self):
        self.alpha_vantage_key = ALPHA_VANTAGE_KEY
        self.finnhub_key = FINNHUB_API_KEY

    def get_alpha_vantage_indicators(self, ticker: str) -> Dict:
        """
        Get pre-computed technical indicators from Alpha Vantage (free tier)
        They compute server-side, we just fetch results
        """
        if not self.alpha_vantage_key:
            return {}

        try:
            # RSI (pre-computed by Alpha Vantage)
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'RSI',
                'symbol': ticker,
                'interval': 'daily',
                'time_period': 14,
                'series_type': 'close',
                'apikey': self.alpha_vantage_key
            }
            response = requests.get(url, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if 'Technical Analysis: RSI' in data:
                    rsi_data = data['Technical Analysis: RSI']
                    latest_date = sorted(rsi_data.keys(), reverse=True)[0]
                    rsi_value = float(rsi_data[latest_date]['RSI'])
                    return {'rsi': rsi_value, 'source': 'alpha_vantage'}

        except Exception as e:
            print(f"Alpha Vantage error: {e}")

        return {}

    def get_finnhub_technical_indicators(self, ticker: str) -> Dict:
        """
        Get pre-computed technicals from Finnhub
        They provide RSI, MACD, SMA, etc. pre-computed
        """
        if not self.finnhub_key:
            return {}

        try:
            # Finnhub supports basic technical indicators
            # For more advanced, we'd need paid tier
            url = f"https://finnhub.io/api/v1/indicator"
            params = {
                'symbol': ticker,
                'resolution': 'D',
                'from': int((datetime.now() - pd.Timedelta(days=100)).timestamp()),
                'to': int(datetime.now().timestamp()),
                'indicator': 'rsi',
                'token': self.finnhub_key
            }
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'rsi' in data:
                    return {
                        'rsi': data['rsi'][-1] if data['rsi'] else None,
                        'source': 'finnhub'
                    }

        except Exception as e:
            print(f"Finnhub technical error: {e}")

        return {}

    def get_tradingview_ideas_sentiment(self, ticker: str) -> Dict:
        """
        Scrape TradingView ideas for sentiment
        TradingView computes popularity/ideas server-side
        """
        try:
            # TradingView public ideas (no API key needed)
            url = f"https://www.tradingview.com/symbols/{ticker}/ideas/"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                # Simple sentiment based on ideas count
                # More ideas = more interest = positive bias
                return {
                    'has_ideas': True,
                    'source': 'tradingview'
                }

        except Exception as e:
            print(f"TradingView scrape error: {e}")

        return {'has_ideas': False}
