"""
Stock Trading Strategies
Combines sentiment, technical, and fundamental analysis
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import requests

from config import STOP_LOSS_ATR_MULTIPLIER, TAKE_PROFIT_RR_RATIO
from utils.sentiment_analyzer import SentimentAnalyzer, TechnicalSentimentAnalyzer
from utils.memory_manager import PredictionMemory


class StockStrategy:
    """Main stock trading strategy using multiple signals"""

    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.tech_sentiment = TechnicalSentimentAnalyzer()
        self.memory = PredictionMemory()

    def analyze_ticker(self, ticker: str, detailed: bool = False) -> Dict:
        """
        Full analysis of a stock
        Returns trading signal based on multiple factors
        """
        # Check memory first (avoid recomputation)
        if not self.memory.should_recompute(ticker, min_hours=12):
            past = self.memory.get_past_predictions(ticker, days=1)
            if past:
                print(f"  Using cached analysis for {ticker}")
                return past[-1]['prediction']

        print(f"  Analyzing {ticker}...")

        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'signal': 'HOLD',
            'confidence': 0.0,
            'factors': {},
            'price_target': None,
            'stop_loss': None,
        }

        try:
            # Fetch stock data
            stock = yf.Ticker(ticker)
            hist = stock.history(period='6mo')

            if hist.empty or len(hist) < 50:
                result['error'] = 'Insufficient data'
                return result

            # 1. Sentiment Analysis (uses pre-computed when possible)
            sentiment = self.sentiment_analyzer.get_aggregate_sentiment(ticker)
            result['factors']['sentiment'] = sentiment

            # 2. Technical Analysis
            tech_signals = self._analyze_technicals(hist)
            result['factors']['technical'] = tech_signals

            # 3. Fundamental Check
            info = stock.info
            result['factors']['fundamentals'] = {
                'pe_ratio': info.get('trailingPE', None),
                'market_cap': info.get('marketCap', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'profit_margin': info.get('profitMargins', 0),
            }

            # 4. Generate Signal
            signal, confidence = self._generate_signal(result['factors'])
            result['signal'] = signal
            result['confidence'] = confidence

            # 5. Price targets
            current_price = hist['Close'].iloc[-1]
            result['current_price'] = round(current_price, 2)

            # ATR-based targets (matches get_swing_trade_setup logic)
            high_low = hist['High'] - hist['Low']
            high_close = np.abs(hist['High'] - hist['Close'].shift())
            low_close = np.abs(hist['Low'] - hist['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            atr = true_range.rolling(14).mean().iloc[-1]

            if signal == 'BUY':
                result['price_target'] = round(current_price + atr * STOP_LOSS_ATR_MULTIPLIER * TAKE_PROFIT_RR_RATIO, 2)
                result['stop_loss'] = round(current_price - atr * STOP_LOSS_ATR_MULTIPLIER, 2)
            elif signal == 'SELL':
                result['price_target'] = round(current_price - atr * STOP_LOSS_ATR_MULTIPLIER * TAKE_PROFIT_RR_RATIO, 2)
                result['stop_loss'] = round(current_price + atr * STOP_LOSS_ATR_MULTIPLIER, 2)

            # 6. Store in memory
            self.memory.add_prediction(ticker, result)

        except Exception as e:
            result['error'] = str(e)
            print(f"Error analyzing {ticker}: {e}")

        return result

    def _analyze_technicals(self, hist: pd.DataFrame) -> Dict:
        """Technical analysis using yfinance data"""
        signals = {}

        # Moving Averages
        ma_20 = hist['Close'].rolling(20).mean().iloc[-1]
        ma_50 = hist['Close'].rolling(50).mean().iloc[-1]
        ma_200 = hist['Close'].rolling(200).mean().iloc[-1] if len(hist) >= 200 else ma_50
        current_price = hist['Close'].iloc[-1]

        signals['ma_signal'] = 'BULLISH' if current_price > ma_20 > ma_50 else 'BEARISH'
        signals['ma_20'] = round(ma_20, 2)
        signals['ma_50'] = round(ma_50, 2)

        # RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        signals['rsi'] = round(current_rsi, 2)
        signals['rsi_signal'] = 'OVERBOUGHT' if current_rsi > 70 else 'OVERSOLD' if current_rsi < 30 else 'NEUTRAL'

        # MACD
        ema_12 = hist['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal_line = macd.ewm(span=9, adjust=False).mean()
        hist_macd = macd - signal_line

        signals['macd'] = round(macd.iloc[-1], 4)
        signals['macd_signal'] = 'BULLISH' if macd.iloc[-1] > signal_line.iloc[-1] else 'BEARISH'

        # Volume
        avg_volume = hist['Volume'].rolling(20).mean().iloc[-1]
        current_volume = hist['Volume'].iloc[-1]
        signals['volume_surge'] = current_volume / avg_volume if avg_volume > 0 else 1
        signals['volume_signal'] = 'HIGH' if signals['volume_surge'] > 1.5 else 'NORMAL'

        return signals

    def _generate_signal(self, factors: Dict) -> tuple:
        """Generate trading signal from all factors"""
        score = 0
        max_score = 6

        # Sentiment (0-2 points)
        sentiment = factors.get('sentiment', {}).get('aggregate_sentiment', 0)
        if sentiment > 0.2:
            score += 2
        elif sentiment > 0.05:
            score += 1
        elif sentiment < -0.2:
            score -= 2
        elif sentiment < -0.05:
            score -= 1

        # Technical signals (0-3 points)
        tech = factors.get('technical', {})

        if tech.get('ma_signal') == 'BULLISH':
            score += 1
        elif tech.get('ma_signal') == 'BEARISH':
            score -= 1

        if tech.get('macd_signal') == 'BULLISH':
            score += 1
        elif tech.get('macd_signal') == 'BEARISH':
            score -= 1

        if tech.get('rsi_signal') == 'OVERSOLD':
            score += 1  # Potential bounce
        elif tech.get('rsi_signal') == 'OVERBOUGHT':
            score -= 1

        # Volume confirmation
        if tech.get('volume_signal') == 'HIGH' and score > 0:
            score += 1  # High volume confirms move

        # Generate signal
        confidence = abs(score) / max_score

        if score >= 3:
            return 'BUY', min(confidence, 1.0)
        elif score <= -3:
            return 'SELL', min(confidence, 1.0)
        else:
            return 'HOLD', confidence

    def get_swing_trade_setup(self, ticker: str) -> Dict:
        """Identify swing trade opportunities"""
        analysis = self.analyze_ticker(ticker)

        if analysis.get('signal') == 'HOLD':
            return {'ticker': ticker, 'setup': None, 'reason': 'No clear signal'}

        hist = yf.Ticker(ticker).history(period='3mo')
        if hist.empty:
            return {'ticker': ticker, 'setup': None, 'reason': 'No data'}

        current_price = hist['Close'].iloc[-1]

        # ATR for stop loss
        high_low = hist['High'] - hist['Low']
        high_close = np.abs(hist['High'] - hist['Close'].shift())
        low_close = np.abs(hist['Low'] - hist['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]

        setup = {
            'ticker': ticker,
            'signal': analysis['signal'],
            'confidence': analysis['confidence'],
            'entry_price': round(current_price, 2),
            'stop_loss': round(current_price - (atr * STOP_LOSS_ATR_MULTIPLIER), 2),
            'take_profit': round(current_price + (atr * STOP_LOSS_ATR_MULTIPLIER * TAKE_PROFIT_RR_RATIO), 2),
            'risk_reward_ratio': TAKE_PROFIT_RR_RATIO,
            'atr': round(atr, 2),
        }

        return setup
