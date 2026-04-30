"""
Stock Screener - Find promising companies using free data
Focuses compute on few high-potential tickers
"""

import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np

from config import *
from utils.data_fetcher import MarketDataFetcher


class SmartScreener:
    """
    Screens thousands of stocks to find few promising ones
    Uses free yfinance data and pre-computed indicators when possible
    """

    def __init__(self):
        self.data_fetcher = MarketDataFetcher()
        self.major_tickers = self._get_major_tickers()

    def _get_major_tickers(self) -> List[str]:
        """Get list of major tickers to screen (focus on known liquid stocks)"""
        # S&P 500 + popular ETFs + hot sectors
        return [
            # Tech Giants
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
            # Tech Growth
            'AMD', 'INTC', 'CRM', 'ORCL', 'ADBE', 'NOW', 'SNOW', 'PLTR',
            # Healthcare
            'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'TMO', 'ABT',
            # Finance
            'JPM', 'BAC', 'GS', 'MS', 'V', 'MA', 'AXP',
            # Consumer
            'WMT', 'COST', 'HD', 'NKE', 'SBUX', 'MCD',
            # Energy/Industrial
            'XOM', 'CVX', 'CAT', 'BA', 'GE', 'HON',
            # ETFs for sector analysis
            'SPY', 'QQQ', 'IWM', 'XLK', 'XLF', 'XLE', 'XLV',
            # Crypto proxies
            'COIN', 'MSTR', 'RIOT', 'MARA'
        ]

    def screen_by_market_cap(self, min_cap: float = 1e9) -> List[str]:
        """Quick filter by market cap using yfinance batch queries"""
        qualified = []

        # Batch process to minimize API calls
        batch_size = 20
        for i in range(0, len(self.major_tickers), batch_size):
            batch = self.major_tickers[i:i+batch_size]
            try:
                # yfinance allows batch download
                data = yf.download(batch, period='1d', progress=False, auto_adjust=True)
                if len(batch) == 1:
                    if data.empty:
                        continue
                    ticker = batch[0]
                    info = yf.Ticker(ticker).info
                    if info.get('marketCap', 0) >= min_cap:
                        qualified.append(ticker)
                else:
                    for ticker in batch:
                        try:
                            info = yf.Ticker(ticker).info
                            if info.get('marketCap', 0) >= min_cap:
                                qualified.append(ticker)
                        except:
                            continue
            except Exception as e:
                print(f"Batch screen error: {e}")
                continue

        return qualified

    def screen_by_momentum(self, tickers: List[str], min_rsi: float = 30, max_rsi: float = 70) -> List[Dict]:
        """Screen for momentum setups using pre-computed RSI when available"""
        results = []

        for ticker in tickers[:50]:  # Limit to top 50 for compute efficiency
            try:
                ticker_obj = yf.Ticker(ticker)
                hist = ticker_obj.history(period='3mo')

                if hist.empty or len(hist) < 20:
                    continue

                # Calculate RSI locally (lightweight)
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                current_rsi = rsi.iloc[-1]

                if pd.isna(current_rsi) or current_rsi < min_rsi or current_rsi > max_rsi:
                    continue

                # Price momentum
                price_change_1m = (hist['Close'].iloc[-1] / hist['Close'].iloc[-22] - 1) if len(hist) >= 22 else 0
                price_change_1w = (hist['Close'].iloc[-1] / hist['Close'].iloc[-5] - 1) if len(hist) >= 5 else 0

                # Volume surge
                avg_volume = hist['Volume'].rolling(20).mean().iloc[-1]
                current_volume = hist['Volume'].iloc[-1]
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

                # Moving averages
                ma_50 = hist['Close'].rolling(50).mean().iloc[-1]
                ma_200 = hist['Close'].rolling(200).mean().iloc[-1] if len(hist) >= 200 else ma_50
                current_price = hist['Close'].iloc[-1]

                # Score the setup
                score = 0
                if price_change_1m > 0: score += 2
                if price_change_1w > 0: score += 1
                if current_price > ma_50: score += 2
                if current_price > ma_200: score += 2
                if volume_ratio > 1.5: score += 1
                if 40 < current_rsi < 60: score += 1  # Not overbought/oversold

                results.append({
                    'ticker': ticker,
                    'score': score,
                    'rsi': round(current_rsi, 2),
                    'price_change_1m': round(price_change_1m * 100, 2),
                    'price_change_1w': round(price_change_1w * 100, 2),
                    'volume_surge': round(volume_ratio, 2),
                    'price': round(current_price, 2),
                    'ma_50': round(ma_50, 2),
                    'ma_200': round(ma_200, 2),
                })

            except Exception as e:
                print(f"Error screening {ticker}: {e}")
                continue

        return sorted(results, key=lambda x: x['score'], reverse=True)

    def screen_by_volatility(self, tickers: List[str], min_atr_pct: float = 0.02) -> List[Dict]:
        """Screen for volatility (good for options trading)"""
        results = []

        for ticker in tickers[:30]:  # Limit for compute
            try:
                hist = yf.Ticker(ticker).history(period='3mo')
                if hist.empty or len(hist) < 14:
                    continue

                # Calculate ATR (Average True Range)
                high_low = hist['High'] - hist['Low']
                high_close = np.abs(hist['High'] - hist['Close'].shift())
                low_close = np.abs(hist['Low'] - hist['Close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = np.max(ranges, axis=1)
                atr = true_range.rolling(14).mean().iloc[-1]
                atr_pct = atr / hist['Close'].iloc[-1]

                if atr_pct >= min_atr_pct:
                    results.append({
                        'ticker': ticker,
                        'atr_pct': round(atr_pct * 100, 2),
                        'price': round(hist['Close'].iloc[-1], 2),
                        'volatility_score': round(atr_pct * 100, 2)
                    })

            except Exception as e:
                continue

        return sorted(results, key=lambda x: x['atr_pct'], reverse=True)

    def get_top_opportunities(self, max_results: int = MAX_TICKERS_TO_ANALYZE) -> List[Dict]:
        """
        Main method: Get top trading opportunities
        Returns only the best few tickers to focus compute on
        """
        print("Screening for top opportunities...")

        # Step 1: Quick market cap filter
        print("  Step 1: Filtering by market cap...")
        qualified = self.screen_by_market_cap(SCREEN_CRITERIA['min_market_cap'])
        print(f"  Qualified tickers after market cap filter: {len(qualified)}")

        # Step 2: Momentum screen
        print("  Step 2: Screening for momentum...")
        momentum_results = self.screen_by_momentum(qualified)
        print(f"  Momentum candidates: {len(momentum_results)}")

        # Step 3: Return top N
        top = momentum_results[:max_results]
        print(f"  Top {len(top)} opportunities identified")

        return top

    def get_sector_performance(self) -> Dict:
        """Get sector ETF performance (pre-computed by Yahoo)"""
        sectors = {
            'Technology': 'XLK',
            'Financials': 'XLF',
            'Healthcare': 'XLV',
            'Energy': 'XLE',
            'Consumer': 'XLP',
            'Industrial': 'XLI',
            'Utilities': 'XLU',
            'Real Estate': 'XLRE'
        }

        performance = {}
        for sector, etf in sectors.items():
            try:
                hist = yf.Ticker(etf).history(period='1mo')
                if not hist.empty:
                    perf = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
                    performance[sector] = round(perf, 2)
            except:
                performance[sector] = 0.0

        return performance
