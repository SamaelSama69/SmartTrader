"""
Options Trading Strategies
Analyzes options flow, unusual activity, and generates options strategies
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from config import *


class OptionsAnalyzer:
    """Options analysis and strategy generation"""

    def __init__(self):
        pass

    def get_options_chain(self, ticker: str) -> Dict:
        """Get options chain data"""
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options

            if not expirations:
                return {'error': 'No options available'}

            # Get nearest expiration with decent volume
            chain_data = None
            selected_exp = None

            for exp in expirations[:5]:
                chain = stock.option_chain(exp)
                calls = chain.calls
                puts = chain.puts

                # Check for volume
                if not calls.empty and calls['volume'].sum() > 100:
                    chain_data = chain
                    selected_exp = exp
                    break

            if not chain_data:
                return {'error': 'No liquid options found'}

            return {
                'ticker': ticker,
                'expiration': selected_exp,
                'calls': self._process_options(calls, 'call'),
                'puts': self._process_options(puts, 'put'),
            }

        except Exception as e:
            return {'error': str(e)}

    def _process_options(self, df: pd.DataFrame, opt_type: str) -> List[Dict]:
        """Process options data"""
        if df.empty:
            return []

        # Filter for liquid options
        df = df[df['volume'] > OPTIONS_MIN_VOLUME]
        df = df[df['openInterest'] > OPTIONS_MIN_OPEN_INTEREST]

        results = []
        for _, row in df.iterrows():
            results.append({
                'strike': row['strike'],
                'last_price': row['lastPrice'],
                'bid': row['bid'],
                'ask': row['ask'],
                'volume': row['volume'],
                'open_interest': row['openInterest'],
                'implied_volatility': row.get('impliedVolatility', 0),
                'type': opt_type,
                'delta': row.get('delta', None),
                'gamma': row.get('gamma', None),
                'theta': row.get('theta', None),
            })

        return sorted(results, key=lambda x: x['volume'], reverse=True)[:20]

    def detect_unusual_options_activity(self, ticker: str) -> Dict:
        """Detect unusual options activity (potential insider moves)"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='30d')
            current_price = hist['Close'].iloc[-1] if not hist.empty else None

            expiration = stock.options[0] if stock.options else None
            if not expiration:
                return {'unusual_activity': False}

            chain = stock.option_chain(expiration)
            calls = chain.calls
            puts = chain.puts

            unusual = []

            # Check for volume spikes in calls
            for _, row in calls.iterrows():
                avg_volume = row.get('openInterest', 0) / 20  # Rough average
                if row['volume'] > avg_volume * UNUSUAL_OPTIONS_VOLUME_MULTIPLIER:
                    unusual.append({
                        'type': 'CALL',
                        'strike': row['strike'],
                        'volume': row['volume'],
                        'avg_volume': round(avg_volume, 0),
                        'signal': 'BULLISH' if current_price and row['strike'] > current_price else 'BEARISH'
                    })

            # Check for volume spikes in puts
            for _, row in puts.iterrows():
                avg_volume = row.get('openInterest', 0) / 20
                if row['volume'] > avg_volume * UNUSUAL_OPTIONS_VOLUME_MULTIPLIER:
                    unusual.append({
                        'type': 'PUT',
                        'strike': row['strike'],
                        'volume': row['volume'],
                        'avg_volume': round(avg_volume, 0),
                        'signal': 'BEARISH'
                    })

            return {
                'ticker': ticker,
                'unusual_activity': len(unusual) > 0,
                'activity_count': len(unusual),
                'activities': unusual[:10],
                'current_price': current_price,
            }

        except Exception as e:
            return {'error': str(e)}

    def suggest_options_strategy(self, ticker: str, direction: str) -> Dict:
        """
        Suggest options strategy based on market outlook
        direction: 'BULLISH', 'BEARISH', 'NEUTRAL'
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='3mo')
            current_price = hist['Close'].iloc[-1]

            # Calculate volatility (for strategy selection)
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized

            # Get nearest expiration
            if not stock.options:
                return {'error': 'No options available'}

            expiration = stock.options[1] if len(stock.options) > 1 else stock.options[0]
            chain = stock.option_chain(expiration)

            strategies = []

            if direction == 'BULLISH':
                strategies = [
                    {
                        'name': 'Long Call',
                        'description': 'Buy call option for direct upside',
                        'risk': 'Limited to premium paid',
                        'best_if': 'Strong bullish move expected',
                    },
                    {
                        'name': 'Bull Call Spread',
                        'description': 'Buy lower strike call, sell higher strike',
                        'risk': 'Limited',
                        'best_if': 'Moderate bullish outlook',
                    },
                    {
                        'name': 'Cash-Secured Put',
                        'description': 'Sell put to acquire stock at lower price',
                        'risk': 'Obligated to buy at strike',
                        'best_if': 'Want to own stock at discount',
                    }
                ]
            elif direction == 'BEARISH':
                strategies = [
                    {
                        'name': 'Long Put',
                        'description': 'Buy put option for downside protection',
                        'risk': 'Limited to premium paid',
                        'best_if': 'Strong bearish move expected',
                    },
                    {
                        'name': 'Bear Put Spread',
                        'description': 'Buy higher strike put, sell lower strike',
                        'risk': 'Limited',
                        'best_if': 'Moderate bearish outlook',
                    }
                ]
            else:  # NEUTRAL
                strategies = [
                    {
                        'name': 'Iron Condor',
                        'description': 'Sell OTM call and put spreads',
                        'risk': 'Limited but capped profit',
                        'best_if': 'Low volatility expected',
                    },
                    {
                        'name': 'Straddle',
                        'description': 'Buy call and put at same strike',
                        'risk': 'Double premium if no move',
                        'best_if': 'Big move expected (any direction)',
                    }
                ]

            return {
                'ticker': ticker,
                'direction': direction,
                'current_price': round(current_price, 2),
                'volatility': round(volatility * 100, 2),
                'suggested_strategies': strategies,
                'expiration': expiration,
            }

        except Exception as e:
            return {'error': str(e)}

    def calculate_options_profit_loss(self, strategy: Dict, exit_price: float) -> Dict:
        """Calculate potential profit/loss for an options strategy"""
        # Simplified P&L calculation
        # In practice, would need full options pricing model
        return {
            'strategy': strategy.get('name'),
            'max_profit': 'Unlimited' if 'Call' in strategy.get('name', '') else 'Limited',
            'max_loss': 'Limited to premium',
            'breakeven': 'Strike + Premium' if 'Call' in strategy.get('name', '') else 'Strike - Premium'
        }
