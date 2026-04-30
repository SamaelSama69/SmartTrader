"""
Futures Trading Strategies
Analyzes futures contracts, spreads, and intermarket relationships
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class FuturesAnalyzer:
    """Futures market analysis"""

    def __init__(self):
        # Futures ETF proxies (since yfinance doesn't have direct futures)
        self.futures_proxies = {
            'ES': 'SPY',  # S&P 500 futures proxy
            'NQ': 'QQQ',  # NASDAQ futures proxy
            'CL': 'USO',  # Crude Oil futures proxy
            'BZ': 'BNO',  # Brent Crude proxy
            'GC': 'GLD',  # Gold futures proxy
            'SI': 'SLV',  # Silver futures proxy
            'ZN': 'IEF',  # 10Y Treasury note proxy
            'ZF': 'SHY',  # 5Y Treasury note proxy
            '6E': 'FXE',  # Euro futures proxy
            '6J': 'FXY',  # Yen futures proxy
            'ZC': 'CORN', # Corn futures proxy
            'ZS': 'SOYB', # Soybeans futures proxy
            'ZW': 'WEAT', # Wheat futures proxy
        }

    def analyze_futures_contract(self, symbol: str) -> Dict:
        """Analyze a futures contract using ETF proxy"""
        proxy = self.futures_proxies.get(symbol)
        if not proxy:
            return {'error': f'No proxy for {symbol}'}

        try:
            ticker = yf.Ticker(proxy)
            hist = ticker.history(period='6mo')

            if hist.empty:
                return {'error': 'No data available'}

            current_price = hist['Close'].iloc[-1]

            # Technical analysis
            ma_20 = hist['Close'].rolling(20).mean().iloc[-1]
            ma_50 = hist['Close'].rolling(50).mean().iloc[-1]

            # Trend
            trend = 'UP' if current_price > ma_20 > ma_50 else 'DOWN'

            # Volatility
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100

            # Volume trend
            avg_volume = hist['Volume'].rolling(20).mean().iloc[-1]
            current_volume = hist['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

            return {
                'symbol': symbol,
                'proxy': proxy,
                'current_price': round(current_price, 2),
                'trend': trend,
                'ma_20': round(ma_20, 2),
                'ma_50': round(ma_50, 2),
                'volatility_pct': round(volatility, 2),
                'volume_ratio': round(volume_ratio, 2),
                'signal': 'BUY' if trend == 'UP' and volume_ratio > 1.2 else 'SELL' if trend == 'DOWN' and volume_ratio > 1.2 else 'HOLD'
            }

        except Exception as e:
            return {'error': str(e)}

    def analyze_intermarket_relationships(self) -> Dict:
        """
        Analyze intermarket relationships
        E.g., Dollar Up = Commodities Down, Bonds vs Stocks, etc.
        """
        results = {}

        try:
            # 1. Dollar vs Gold (inverse relationship)
            dollar = yf.Ticker('UUP')  # Dollar ETF
            gold = yf.Ticker('GLD')

            d_hist = dollar.history(period='3mo')
            g_hist = gold.history(period='3mo')

            if not d_hist.empty and not g_hist.empty:
                d_change = (d_hist['Close'].iloc[-1] / d_hist['Close'].iloc[0] - 1) * 100
                g_change = (g_hist['Close'].iloc[-1] / g_hist['Close'].iloc[0] - 1) * 100

                results['dollar_gold'] = {
                    'dollar_change_pct': round(d_change, 2),
                    'gold_change_pct': round(g_change, 2),
                    'relationship': 'NORMAL' if (d_change > 0 and g_change < 0) or (d_change < 0 and g_change > 0) else 'ABNORMAL'
                }

            # 2. Bonds vs Stocks (usually inverse)
            bonds = yf.Ticker('TLT')  # 20Y Treasury
            stocks = yf.Ticker('SPY')

            b_hist = bonds.history(period='3mo')
            s_hist = stocks.history(period='3mo')

            if not b_hist.empty and not s_hist.empty:
                b_change = (b_hist['Close'].iloc[-1] / b_hist['Close'].iloc[0] - 1) * 100
                s_change = (s_hist['Close'].iloc[-1] / s_hist['Close'].iloc[0] - 1) * 100

                results['bonds_stocks'] = {
                    'bonds_change_pct': round(b_change, 2),
                    'stocks_change_pct': round(s_change, 2),
                    'relationship': 'NORMAL' if (b_change < 0 and s_change > 0) or (b_change > 0 and s_change < 0) else 'RISK_ON'
                }

            # 3. Crude Oil vs Energy Stocks
            oil = yf.Ticker('USO')
            energy = yf.Ticker('XLE')  # Energy sector ETF

            o_hist = oil.history(period='3mo')
            e_hist = energy.history(period='3mo')

            if not o_hist.empty and not e_hist.empty:
                o_change = (o_hist['Close'].iloc[-1] / o_hist['Close'].iloc[0] - 1) * 100
                e_change = (e_hist['Close'].iloc[-1] / e_hist['Close'].iloc[0] - 1) * 100

                results['oil_energy'] = {
                    'oil_change_pct': round(o_change, 2),
                    'energy_change_pct': round(e_change, 2),
                    'divergence': abs(o_change - e_change) > 10  # 10% divergence
                }

        except Exception as e:
            results['error'] = str(e)

        return results

    def get_futures_spread_opportunity(self) -> List[Dict]:
        """Identify futures spread trading opportunities"""
        opportunities = []

        # Example: Check Gold vs Silver ratio
        try:
            gold = yf.Ticker('GLD')
            silver = yf.Ticker('SLV')

            g_hist = gold.history(period='1y')
            s_hist = silver.history(period='1y')

            if not g_hist.empty and not s_hist.empty:
                g_price = g_hist['Close'].iloc[-1]
                s_price = s_hist['Close'].iloc[-1]

                # Gold/Silver ratio
                ratio = g_price / s_price

                # Historical average around 80
                if ratio > 85:
                    opportunities.append({
                        'spread': 'Gold/Silver',
                        'ratio': round(ratio, 2),
                        'signal': 'SELL GOLD / BUY SILVER',
                        'reason': 'Ratio above historical average'
                    })
                elif ratio < 75:
                    opportunities.append({
                        'spread': 'Gold/Silver',
                        'ratio': round(ratio, 2),
                        'signal': 'BUY GOLD / SELL SILVER',
                        'reason': 'Ratio below historical average'
                    })

        except Exception as e:
            print(f"Spread analysis error: {e}")

        return opportunities

    def generate_futures_signal(self, symbol: str) -> Dict:
        """Generate futures trading signal"""
        analysis = self.analyze_futures_contract(symbol)

        if 'error' in analysis:
            return analysis

        # Get intermarket context
        intermarket = self.analyze_intermarket_relationships()

        signal = analysis.get('signal', 'HOLD')

        # Modify signal based on intermarket
        if symbol == 'GC':  # Gold
            dollar_gold = intermarket.get('dollar_gold', {})
            if dollar_gold.get('dollar_change_pct', 0) < -2:
                signal = 'BUY'  # Dollar down = Gold up
            elif dollar_gold.get('dollar_change_pct', 0) > 2:
                signal = 'SELL'

        return {
            'symbol': symbol,
            'signal': signal,
            'confidence': 0.7 if signal != 'HOLD' else 0.3,
            'analysis': analysis,
            'intermarket_context': intermarket,
            'timestamp': datetime.now().isoformat()
        }
