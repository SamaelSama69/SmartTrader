"""
Expert Tracker - Tracks ratings and predictions from experts and publications
Weighs their opinions based on historical accuracy
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import time

from config import *
from utils.data_fetcher import MarketDataFetcher


class ExpertTracker:
    """
    Tracks expert predictions and ratings
    Weighs opinions based on historical accuracy
    """

    def __init__(self):
        self.data_fetcher = MarketDataFetcher()
        self.experts_file = MEMORY_DIR / "experts_tracking.json"
        self.experts_data = self._load_experts_data()

        # Well-known experts and publications to track
        self.tracked_experts = {
            # Analysts (from Finnhub)
            'analyst_strong_buy': {'type': 'analyst', 'weight': 1.0, 'accuracy': 0.5},
            'analyst_buy': {'type': 'analyst', 'weight': 0.8, 'accuracy': 0.5},
            'analyst_hold': {'type': 'analyst', 'weight': 0.5, 'accuracy': 0.5},
            'analyst_sell': {'type': 'analyst', 'weight': 0.8, 'accuracy': 0.5},

            # Publications (scraped/API)
            'motley_fool': {'type': 'publication', 'weight': 0.7, 'accuracy': 0.5},
            'seeking_alpha': {'type': 'publication', 'weight': 0.6, 'accuracy': 0.5},
            'barrons': {'type': 'publication', 'weight': 0.8, 'accuracy': 0.5},
            'bloomberg': {'type': 'publication', 'weight': 0.9, 'accuracy': 0.5},
            'wsj': {'type': 'publication', 'weight': 0.85, 'accuracy': 0.5},

            # Notable Investors (tracked via news sentiment)
            'buffett': {'type': 'investor', 'weight': 1.0, 'accuracy': 0.5},
            'wood_cathie': {'type': 'investor', 'weight': 0.8, 'accuracy': 0.5},
        }

    def _load_experts_data(self) -> Dict:
        """Load expert tracking data from disk"""
        if self.experts_file.exists():
            try:
                with open(self.experts_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'experts': {},
            'predictions': [],
            'outcomes': [],
            'last_update': '',
            'metadata': {}
        }

    def save(self):
        """Save experts data to disk"""
        with open(self.experts_file, 'w') as f:
            json.dump(self.experts_data, f, indent=2, default=str)

    def get_finnhub_analyst_ratings(self, ticker: str) -> Dict:
        """
        Get analyst ratings from Finnhub (pre-computed, free tier)
        These are professional analyst recommendations
        """
        if not FINNHUB_API_KEY:
            return {'error': 'No Finnhub API key'}

        try:
            # Get analyst recommendations
            url = f"https://finnhub.io/api/v1/stock/recommendation"
            params = {'symbol': ticker, 'token': FINNHUB_API_KEY}
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if not data:
                    return {'ratings': [], 'consensus': 'HOLD'}

                # Get latest recommendations
                latest = data[0] if data else {}

                # Calculate consensus
                buy_count = latest.get('buy', 0) + latest.get('strongBuy', 0)
                sell_count = latest.get('sell', 0) + latest.get('strongSell', 0)
                hold_count = latest.get('hold', 0)

                total = buy_count + sell_count + hold_count

                if total > 0:
                    buy_pct = (buy_count / total) * 100
                    sell_pct = (sell_count / total) * 100
                    hold_pct = (hold_count / total) * 100

                    if buy_pct > 50:
                        consensus = 'BUY'
                    elif sell_pct > 50:
                        consensus = 'SELL'
                    else:
                        consensus = 'HOLD'

                    return {
                        'ratings': data[:4],  # Last 4 weeks
                        'consensus': consensus,
                        'buy_count': buy_count,
                        'sell_count': sell_count,
                        'hold_count': hold_count,
                        'buy_pct': round(buy_pct, 1),
                        'sell_pct': round(sell_pct, 1),
                        'hold_pct': round(hold_pct, 1),
                        'source': 'finnhub_analysts'
                    }

        except Exception as e:
            print(f"Finnhub analyst ratings error: {e}")

        return {'ratings': [], 'consensus': 'HOLD'}

    def get_analyst_price_targets(self, ticker: str) -> Dict:
        """Get analyst price targets from Yahoo Finance (free)"""
        try:
            ticker_obj = yf.Ticker(ticker)
            info = ticker_obj.info

            return {
                'ticker': ticker,
                'current_price': info.get('currentPrice') or info.get('regularMarketPrice', 0),
                'target_high': info.get('targetHighPrice', None),
                'target_low': info.get('targetLowPrice', None),
                'target_mean': info.get('targetMeanPrice', None),
                'target_median': info.get('targetMedianPrice', None),
                'number_of_analysts': info.get('numberOfAnalystOpinions', 0),
                'upside_pct': round(((info.get('targetMeanPrice', 0) / (info.get('currentPrice') or 1) - 1) * 100), 2) if info.get('currentPrice') else 0,
                'source': 'yahoo_finance_analysts'
            }

        except Exception as e:
            print(f"Analyst price targets error: {e}")
            return {}

    def get_news_expert_mentions(self, ticker: str, days: int = 30) -> Dict:
        """
        Scrape news for expert mentions and opinions
        Tracks what experts are saying about a stock
        """
        try:
            # Fetch news from multiple sources
            ticker_obj = yf.Ticker(ticker)
            news = ticker_obj.news

            if not news:
                return {'expert_mentions': []}

            expert_keywords = {
                'buffett': ['warren buffett', 'berkshire hathaway', 'buffett'],
                'wood_cathie': ['cathie wood', 'ark invest', 'wood'],
                'dalio': ['ray dalio', 'bridgewater', 'dalio'],
                'ackman': ['bill ackman', 'pershing square', 'ackman'],
                'burry': ['michael burry', 'scion', 'burry'],
            }

            mentions = []

            for article in news[:50]:  # Last 50 news items
                title = article.get('title', '').lower()
                text = (title + ' ' + article.get('text', '')).lower()

                for expert, keywords in expert_keywords.items():
                    for keyword in keywords:
                        if keyword in text:
                            # Determine sentiment
                            sentiment = self._extract_sentiment(text, ticker)
                            mentions.append({
                                'expert': expert,
                                'article_title': article.get('title', ''),
                                'sentiment': sentiment,
                                'date': datetime.fromtimestamp(article.get('providerPublishTime', 0)).isoformat(),
                                'url': article.get('link', '')
                            })
                            break

            # Aggregate by expert
            expert_summary = {}
            for mention in mentions:
                expert = mention['expert']
                if expert not in expert_summary:
                    expert_summary[expert] = {'mentions': 0, 'avg_sentiment': 0.0, 'latest_date': ''}
                expert_summary[expert]['mentions'] += 1
                expert_summary[expert]['avg_sentiment'] += mention['sentiment']
                if mention['date'] > expert_summary[expert].get('latest_date', ''):
                    expert_summary[expert]['latest_date'] = mention['date']

            # Calculate average sentiment
            for expert in expert_summary:
                if expert_summary[expert]['mentions'] > 0:
                    expert_summary[expert]['avg_sentiment'] /= expert_summary[expert]['mentions']
                    expert_summary[expert]['signal'] = 'BUY' if expert_summary[expert]['avg_sentiment'] > 0.1 else 'SELL' if expert_summary[expert]['avg_sentiment'] < -0.1 else 'HOLD'

            return {
                'ticker': ticker,
                'expert_mentions': mentions,
                'expert_summary': expert_summary,
                'total_mentions': len(mentions)
            }

        except Exception as e:
            print(f"Expert mentions error: {e}")
            return {'expert_mentions': []}

    def _extract_sentiment(self, text: str, ticker: str) -> float:
        """Extract sentiment about a ticker from text"""
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        return analyzer.polarity_scores(text)['compound']

    def get_weighted_expert_consensus(self, ticker: str) -> Dict:
        """
        Get weighted expert consensus
        WEIGHTS opinions based on historical accuracy
        """
        print(f"  Fetching expert opinions for {ticker}...")

        consensus_data = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'weighted_score': 0.0,
            'total_weight': 0.0,
            'consensus': 'HOLD',
            'confidence': 0.0
        }

        # 1. Analyst Ratings (Finnhub)
        analyst_ratings = self.get_finnhub_analyst_ratings(ticker)
        if 'consensus' in analyst_ratings:
            consensus_data['sources']['analysts'] = analyst_ratings

            # Convert consensus to score
            score_map = {'BUY': 1.0, 'HOLD': 0.0, 'SELL': -1.0}
            score = score_map.get(analyst_ratings['consensus'], 0.0)
            weight = 0.8  # Analysts have high weight

            consensus_data['weighted_score'] += score * weight
            consensus_data['total_weight'] += weight

        # 2. Price Targets
        price_targets = self.get_analyst_price_targets(ticker)
        if 'upside_pct' in price_targets:
            consensus_data['sources']['price_targets'] = price_targets

            # Score based on upside
            upside = price_targets['upside_pct']
            score = min(max(upside / 20.0, -1.0), 1.0)  # Normalize to [-1, 1]
            weight = 0.7

            consensus_data['weighted_score'] += score * weight
            consensus_data['total_weight'] += weight

        # 3. Expert Mentions in News
        expert_mentions = self.get_news_expert_mentions(ticker)
        if expert_mentions.get('expert_summary'):
            consensus_data['sources']['expert_mentions'] = expert_mentions

            for expert, data in expert_mentions['expert_summary'].items():
                # Check expert's historical accuracy
                expert_accuracy = self._get_expert_accuracy(expert)
                weight = expert_accuracy * 1.0  # Scale by accuracy

                score = data['avg_sentiment']  # Already in [-1, 1]
                consensus_data['weighted_score'] += score * weight
                consensus_data['total_weight'] += weight

        # Calculate final consensus
        if consensus_data['total_weight'] > 0:
            final_score = consensus_data['weighted_score'] / consensus_data['total_weight']
            consensus_data['consensus'] = 'BUY' if final_score > 0.2 else 'SELL' if final_score < -0.2 else 'HOLD'
            consensus_data['confidence'] = abs(final_score)
            consensus_data['score'] = round(final_score, 3)

        return consensus_data

    def _get_expert_accuracy(self, expert_name: str) -> float:
        """
        Get historical accuracy of an expert
        Returns value between 0 and 1
        """
        # Check if we have tracking data
        if expert_name in self.experts_data.get('experts', {}):
            expert_data = self.experts_data['experts'][expert_name]
            total = expert_data.get('correct', 0) + expert_data.get('incorrect', 0)
            if total > 0:
                return expert_data['correct'] / total

        # Default to 0.5 (unknown accuracy)
        return 0.5

    def record_expert_prediction(self, expert_name: str, ticker: str, signal: str, date: str = None):
        """Record an expert's prediction for later verification"""
        if date is None:
            date = datetime.now().isoformat()

        prediction = {
            'expert': expert_name,
            'ticker': ticker,
            'signal': signal,
            'date': date,
            'verified': False,
            'correct': None
        }

        self.experts_data['predictions'].append(prediction)
        self.save()

    def verify_expert_predictions(self, days_back: int = 30):
        """
        Verify past expert predictions against actual stock performance
        Updates expert accuracy scores
        """
        cutoff = datetime.now() - timedelta(days=days_back)

        unverified = [p for p in self.experts_data['predictions']
                      if not p['verified'] and datetime.fromisoformat(p['date']) < cutoff]

        print(f"Verifying {len(unverified)} expert predictions...")

        for pred in unverified:
            try:
                ticker = pred['ticker']
                pred_date = datetime.fromisoformat(pred['date'])

                # Get stock performance since prediction
                hist = yf.Ticker(ticker).history(start=pred_date.strftime('%Y-%m-%d'), period='1mo')

                if hist.empty or len(hist) < 5:
                    continue

                price_change = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100

                # Check if prediction was correct
                signal = pred['signal']
                correct = False

                if signal == 'BUY' and price_change > 0:
                    correct = True
                elif signal == 'SELL' and price_change < 0:
                    correct = True
                elif signal == 'HOLD' and abs(price_change) < 2:
                    correct = True

                # Update prediction
                pred['verified'] = True
                pred['correct'] = correct
                pred['actual_return'] = round(price_change, 2)

                # Update expert accuracy
                expert = pred['expert']
                if expert not in self.experts_data['experts']:
                    self.experts_data['experts'][expert] = {'correct': 0, 'incorrect': 0, 'total': 0}

                if correct:
                    self.experts_data['experts'][expert]['correct'] += 1
                else:
                    self.experts_data['experts'][expert]['incorrect'] += 1
                self.experts_data['experts'][expert]['total'] += 1

            except Exception as e:
                print(f"Error verifying prediction: {e}")
                continue

        self.save()
        print("Expert prediction verification complete.")

    def get_expert_leaderboard(self) -> List[Dict]:
        """Get leaderboard of most accurate experts"""
        leaderboard = []

        for expert, data in self.experts_data.get('experts', {}).items():
            total = data.get('total', 0)
            if total > 0:
                accuracy = (data.get('correct', 0) / total) * 100
                leaderboard.append({
                    'expert': expert,
                    'accuracy': round(accuracy, 1),
                    'correct': data.get('correct', 0),
                    'incorrect': data.get('incorrect', 0),
                    'total_predictions': total
                })

        return sorted(leaderboard, key=lambda x: x['accuracy'], reverse=True)
