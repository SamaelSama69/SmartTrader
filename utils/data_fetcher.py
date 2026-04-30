"""
Data Fetcher - Free market data from multiple sources
Uses yfinance, News API, Reddit, Finnhub (free tiers)
"""

import yfinance as yf
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import praw
from config import *

class MarketDataFetcher:
    """Fetch stock market data using free sources"""

    def __init__(self):
        self.session = requests.Session()
        self.news_analyzer = SentimentIntensityAnalyzer()

    def get_stock_data(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """Fetch historical stock data from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            if df.empty:
                return pd.DataFrame()
            df.reset_index(inplace=True)
            return df
        except Exception as e:
            print(f"Error fetching stock data for {ticker}: {e}")
            return pd.DataFrame()

    def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current/live price"""
        try:
            stock = yf.Ticker(ticker)
            return stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')
        except:
            return None

    def get_options_chain(self, ticker: str) -> Dict:
        """Fetch options chain data"""
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options
            if not expirations:
                return {}

            options_data = {}
            for exp in expirations[:5]:  # Limit to 5 nearest expirations
                chain = stock.option_chain(exp)
                options_data[exp] = {
                    'calls': chain.calls,
                    'puts': chain.puts
                }
            return options_data
        except Exception as e:
            print(f"Error fetching options for {ticker}: {e}")
            return {}

    def get_company_info(self, ticker: str) -> Dict:
        """Get company fundamentals"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', None),
                'forward_pe': info.get('forwardPE', None),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', None),
                '52w_high': info.get('fiftyTwoWeekHigh', None),
                '52w_low': info.get('fiftyTwoWeekLow', None),
                'avg_volume': info.get('averageVolume', 0),
                'revenue_growth': info.get('revenueGrowth', None),
                'profit_margin': info.get('profitMargins', None),
            }
        except Exception as e:
            print(f"Error fetching company info for {ticker}: {e}")
            return {}


class NewsFetcher:
    """Fetch news from multiple free sources"""

    def __init__(self):
        self.news_api_key = NEWS_API_KEY
        self.finnhub_key = FINNHUB_API_KEY

    def get_newsapi_news(self, ticker: str, days: int = 7) -> List[Dict]:
        """Fetch news from News API (free: 100/day)"""
        if not self.news_api_key:
            return []

        try:
            from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            url = f"https://newsapi.org/v2/everything"
            params = {
                'q': ticker,
                'from': from_date,
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.news_api_key,
                'pageSize': NEWS_LIMIT_PER_SOURCE
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                return [{
                    'title': a.get('title', ''),
                    'description': a.get('description', ''),
                    'url': a.get('url', ''),
                    'published_at': a.get('publishedAt', ''),
                    'source': a.get('source', {}).get('name', 'NewsAPI')
                } for a in articles]
        except Exception as e:
            print(f"NewsAPI error: {e}")
        return []

    def get_finnhub_news(self, ticker: str, days: int = 7) -> List[Dict]:
        """Fetch news from Finnhub (free: 60/min)"""
        if not self.finnhub_key:
            return []

        try:
            from_ts = int((datetime.now() - timedelta(days=days)).timestamp())
            to_ts = int(datetime.now().timestamp())
            url = f"https://finnhub.io/api/v1/company-news"
            params = {
                'symbol': ticker,
                'from': datetime.fromtimestamp(from_ts).strftime('%Y-%m-%d'),
                'to': datetime.now().strftime('%Y-%m-%d'),
                'token': self.finnhub_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                articles = response.json()
                return [{
                    'title': a.get('headline', ''),
                    'description': a.get('summary', ''),
                    'url': a.get('url', ''),
                    'published_at': datetime.fromtimestamp(a.get('datetime', 0)).isoformat(),
                    'source': 'Finnhub'
                } for a in articles[:NEWS_LIMIT_PER_SOURCE]]
        except Exception as e:
            print(f"Finnhub error: {e}")
        return []

    def get_yahoo_news(self, ticker: str) -> List[Dict]:
        """Scrape Yahoo Finance news (no API key needed)"""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            if news:
                return [{
                    'title': n.get('title', ''),
                    'description': n.get('text', ''),
                    'url': n.get('link', ''),
                    'published_at': datetime.fromtimestamp(n.get('providerPublishTime', 0)).isoformat(),
                    'source': 'Yahoo Finance'
                } for n in news[:NEWS_LIMIT_PER_SOURCE]]
        except Exception as e:
            print(f"Yahoo News error: {e}")
        return []

    def get_all_news(self, ticker: str, days: int = 7) -> List[Dict]:
        """Aggregate news from all free sources"""
        all_news = []
        seen_titles = set()

        # Fetch from multiple sources
        sources = [
            self.get_newsapi_news(ticker, days),
            self.get_finnhub_news(ticker, days),
            self.get_yahoo_news(ticker)
        ]

        for source_news in sources:
            for article in source_news:
                title = article.get('title', '').lower()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_news.append(article)

        return sorted(all_news, key=lambda x: x.get('published_at', ''), reverse=True)


class RedditSentimentFetcher:
    """Fetch sentiment from Reddit (free, no API key needed for read)"""

    def __init__(self):
        if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
            try:
                self.reddit = praw.Reddit(
                    client_id=REDDIT_CLIENT_ID,
                    client_secret=REDDIT_CLIENT_SECRET,
                    user_agent=REDDIT_USER_AGENT
                )
            except:
                self.reddit = None
        else:
            self.reddit = None

    def get_ticker_mentions(self, ticker: str, subreddits: List[str] = None) -> Dict:
        """Get ticker mentions and sentiment from Reddit"""
        if not self.reddit:
            return {'mentions': 0, 'sentiment': 0.0, 'posts': []}

        if subreddits is None:
            subreddits = ['wallstreetbets', 'stocks', 'investing', 'SecurityAnalysis']

        results = {'mentions': 0, 'sentiment': 0.0, 'posts': []}
        analyzer = SentimentIntensityAnalyzer()

        try:
            for sub_name in subreddits:
                subreddit = self.reddit.subreddit(sub_name)
                for submission in subreddit.search(ticker, limit=25, time_filter='week'):
                    results['mentions'] += 1
                    sentiment = analyzer.polarity_scores(submission.title + ' ' + submission.selftext)
                    results['sentiment'] += sentiment['compound']

                    results['posts'].append({
                        'title': submission.title,
                        'score': submission.score,
                        'sentiment': sentiment['compound'],
                        'url': f"https://reddit.com{submission.permalink}",
                        'created': datetime.fromtimestamp(submission.created_utc).isoformat()
                    })

            if results['mentions'] > 0:
                results['sentiment'] /= results['mentions']

        except Exception as e:
            print(f"Reddit error: {e}")

        return results
