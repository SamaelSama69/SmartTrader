"""
Prebuilt Algorithm Strategies
Based on real profitable traders and platforms like Bulls AI
Includes Indian market-specific algorithms
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from utils.indian_indicators import calculate_vwap, calculate_supertrend, calculate_cpr, is_expiry_day, is_budget_day
from utils.nse_data import convert_to_nse_format


class BaseAlgorithm:
    """Base class for all trading algorithms"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.signals = []

    def analyze(self, ticker: str, hist: pd.DataFrame) -> Dict:
        """Analyze ticker and return signal"""
        raise NotImplementedError

    def get_score(self, ticker: str, hist: pd.DataFrame) -> float:
        """Return confidence score (0-1)"""
        raise NotImplementedError


class BuffettValueAlgorithm(BaseAlgorithm):
    """
    Warren Buffett Value Strategy
    - Focus on quality companies with moat
    - Low P/E, consistent growth, strong ROE
    - "Be fearful when others are greedy, greedy when others are fearful"
    """

    def __init__(self):
        super().__init__(
            "Buffett Value",
            "Value investing strategy focusing on quality companies with strong fundamentals"
        )

    def analyze(self, ticker: str, hist: pd.DataFrame = None) -> Dict:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Value metrics
            pe_ratio = info.get('trailingPE', 999)
            forward_pe = info.get('forwardPE', 999)
            roe = info.get('returnOnEquity', 0)
            debt_to_equity = info.get('debtToEquity', 999)
            profit_margin = info.get('profitMargins', 0)

            # Buffett criteria
            score = 0
            signals = []

            # 1. Reasonable P/E (< 20)
            if pe_ratio and pe_ratio < 15:
                score += 2
                signals.append("Low P/E ratio")
            elif pe_ratio and pe_ratio < 20:
                score += 1

            # 2. Strong ROE (> 15%)
            if roe and roe > 0.20:
                score += 2
                signals.append("Strong ROE")
            elif roe and roe > 0.15:
                score += 1

            # 3. Low debt
            if debt_to_equity and debt_to_equity < 0.5:
                score += 1
                signals.append("Low debt")

            # 4. Consistent profit margins
            if profit_margin and profit_margin > 0.15:
                score += 1
                signals.append("High profit margin")

            # 5. Long-term price trend (200-day MA)
            if hist is not None and len(hist) >= 200:
                ma_200 = hist['Close'].rolling(200).mean().iloc[-1]
                current = hist['Close'].iloc[-1]
                if current > ma_200:
                    score += 1
                    signals.append("Above 200-day MA")

            # Generate signal
            max_score = 7
            confidence = min(score / max_score, 1.0)

            if score >= 4:
                signal = 'BUY'
            elif score <= 2:
                signal = 'SELL'
            else:
                signal = 'HOLD'

            return {
                'algorithm': self.name,
                'signal': signal,
                'confidence': confidence,
                'score': score,
                'max_score': max_score,
                'signals': signals,
                'metrics': {
                    'pe_ratio': pe_ratio,
                    'forward_pe': forward_pe,
                    'roe': roe,
                    'profit_margin': profit_margin,
                    'debt_to_equity': debt_to_equity
                }
            }

        except Exception as e:
            return {'error': str(e)}


class DalioAllWeatherAlgorithm(BaseAlgorithm):
    """
    Ray Dalio's All-Weather Strategy
    - Risk parity approach
    - Works in all economic environments
    - Balanced exposure to growth/inflation scenarios
    """

    def __init__(self):
        super().__init__(
            "Dalio All-Weather",
            "Risk-parity strategy for all economic conditions"
        )

    def analyze(self, ticker: str, hist: pd.DataFrame = None) -> Dict:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Look at asset type (stock vs ETF)
            is_etf = info.get('quoteType', '') == 'ETF'

            score = 0
            signals = []

            if is_etf:
                # For ETFs, check diversification
                category = info.get('category', '').lower()

                # Favor broad market ETFs
                if 's&p' in category or 'total market' in category:
                    score += 2
                    signals.append("Broad market exposure")
                elif 'bond' in category or 'treasury' in category:
                    score += 1
                    signals.append("Fixed income exposure")
                elif 'commodity' in category or 'gold' in category:
                    score += 1
                    signals.append("Inflation hedge")
            else:
                # For stocks, check stability
                beta = info.get('beta', 1.0)
                volatility = info.get('volatility', 0)

                if beta and beta < 1.0:
                    score += 1
                    signals.append("Low beta (defensive)")

                if volatility and volatility < 0.20:
                    score += 1
                    signals.append("Low volatility")

                # Consistent dividend
                div_yield = info.get('dividendYield', 0)
                if div_yield and div_yield > 0.02:
                    score += 1
                    signals.append("Pays dividend")

            # Check correlation to market (simplified)
            if hist is not None and len(hist) >= 60:
                returns = hist['Close'].pct_change().dropna()
                market = yf.Ticker('SPY').history(period='3mo')['Close'].pct_change().dropna()

                if len(returns) > 0 and len(market) > 0:
                    # Align dates
                    min_len = min(len(returns), len(market))
                    corr = returns.iloc[-min_len:].corr(market.iloc[-min_len:])
                    if corr < 0.5:
                        score += 1
                        signals.append("Low market correlation")

            confidence = min(score / 5, 1.0)

            if score >= 3:
                signal = 'BUY'
            elif score <= 1:
                signal = 'SELL'
            else:
                signal = 'HOLD'

            return {
                'algorithm': self.name,
                'signal': signal,
                'confidence': confidence,
                'score': score,
                'signals': signals,
                'diversification_score': score
            }

        except Exception as e:
            return {'error': str(e)}


class BullsAIStyleAlgorithm(BaseAlgorithm):
    """
    Bulls AI-Inspired Momentum Algorithm
    - Trend following with AI signals
    - Volume confirmation
    - Multiple timeframe analysis
    - "The trend is your friend until it ends"
    """

    def __init__(self):
        super().__init__(
            "Bulls AI Momentum",
            "AI-inspired momentum strategy with volume confirmation"
        )

    def analyze(self, ticker: str, hist: pd.DataFrame = None) -> Dict:
        try:
            if hist is None:
                hist = yf.Ticker(ticker).history(period='6mo')

            if hist.empty or len(hist) < 50:
                return {'error': 'Insufficient data'}

            score = 0
            signals = []

            # 1. Trend confirmation (multiple MAs)
            ma_20 = hist['Close'].rolling(20).mean().iloc[-1]
            ma_50 = hist['Close'].rolling(50).mean().iloc[-1]
            ma_200 = hist['Close'].rolling(200).mean().iloc[-1] if len(hist) >= 200 else ma_50

            current = hist['Close'].iloc[-1]

            if current > ma_20 > ma_50 > ma_200:
                score += 3
                signals.append("Strong uptrend (price > MA20 > MA50 > MA200)")
            elif current > ma_20 > ma_50:
                score += 2
                signals.append("Uptrend confirmed")
            elif current < ma_20 < ma_50:
                score -= 2
                signals.append("Downtrend confirmed")

            # 2. Volume confirmation
            avg_volume = hist['Volume'].rolling(20).mean().iloc[-1]
            current_volume = hist['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

            if volume_ratio > 2.0:
                score += 2
                signals.append(f"High volume surge ({volume_ratio:.1f}x)")
            elif volume_ratio > 1.5:
                score += 1
                signals.append("Volume above average")

            # 3. Momentum (RSI)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]

            if 50 < current_rsi < 70:
                score += 2
                signals.append("RSI in sweet spot (50-70)")
            elif current_rsi > 80:
                score -= 1  # Overbought
                signals.append("Overbought (RSI > 80)")
            elif current_rsi < 30:
                score -= 1
                signals.append("Oversold (potential bounce)")

            # 4. MACD
            ema_12 = hist['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = hist['Close'].ewm(span=26, adjust=False).mean()
            macd = ema_12 - ema_26
            signal_line = macd.ewm(span=9, adjust=False).mean()

            if macd.iloc[-1] > signal_line.iloc[-1] and macd.iloc[-2] <= signal_line.iloc[-2]:
                score += 2
                signals.append("MACD bullish crossover")
            elif macd.iloc[-1] < signal_line.iloc[-1] and macd.iloc[-2] >= signal_line.iloc[-2]:
                score -= 2
                signals.append("MACD bearish crossover")

            # Generate signal
            confidence = abs(score) / 7.0

            if score >= 4:
                signal = 'BUY'
            elif score <= -3:
                signal = 'SELL'
            else:
                signal = 'HOLD'

            return {
                'algorithm': self.name,
                'signal': signal,
                'confidence': min(confidence, 1.0),
                'score': score,
                'signals': signals,
                'metrics': {
                    'rsi': round(current_rsi, 2),
                    'macd': round(macd.iloc[-1], 4),
                    'volume_ratio': round(volume_ratio, 2),
                    'ma_20': round(ma_20, 2),
                    'ma_50': round(ma_50, 2),
                }
            }

        except Exception as e:
            return {'error': str(e)}


class WoodDisruptiveGrowthAlgorithm(BaseAlgorithm):
    """
    Cathie Wood ARK-Style Disruptive Growth
    - Focus on disruptive innovation
    - High growth, scalable tech
    "Buy the future at a discount"
    """

    def __init__(self):
        super().__init__(
            "Wood Disruptive Growth",
            "ARK-style strategy focusing on disruptive technology and innovation"
        )

    def analyze(self, ticker: str, hist: pd.DataFrame = None) -> Dict:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            score = 0
            signals = []

            # 1. Sector check (tech, healthare, innovation)
            sector = info.get('sector', '').lower()
            industry = info.get('industry', '').lower()

            innovation_keywords = ['tech', 'software', 'ai', 'biotech', 'genomic', 'robot', 'cloud', 'fintech']

            if any(kw in sector or kw in industry for kw in innovation_keywords):
                score += 2
                signals.append("Disruptive sector/industry")

            # 2. Revenue growth
            revenue_growth = info.get('revenueGrowth', 0)
            if revenue_growth and revenue_growth > 0.30:
                score += 2
                signals.append(f"High revenue growth ({revenue_growth*100:.0f}%)")
            elif revenue_growth and revenue_growth > 0.20:
                score += 1

            # 3. Forward P/E (growth premium is OK)
            forward_pe = info.get('forwardPE', 999)
            if forward_pe and 15 < forward_pe < 40:
                score += 1
                signals.append("Reasonable forward P/E for growth")

            # 4. Price momentum (6-month)
            if hist is not None and len(hist) >= 126:  # ~6 months
                price_change = (hist['Close'].iloc[-1] / hist['Close'].iloc[-126] - 1) * 100
                if price_change > 20:
                    score += 1
                    signals.append(f"Strong 6M momentum (+{price_change:.0f}%)")
                elif price_change < -20:
                    score -= 1
                    signals.append(f"Down 20%+ (potential value)")

            # 5. Market cap (prefer mid-cap for growth)
            market_cap = info.get('marketCap', 0)
            if 1e9 < market_cap < 1e11:  # $1B - $100B
                score += 1
                signals.append("Mid-cap sweet spot")

            confidence = min(score / 6, 1.0)

            if score >= 4:
                signal = 'BUY'
            elif score <= 1:
                signal = 'SELL'
            else:
                signal = 'HOLD'

            return {
                'algorithm': self.name,
                'signal': signal,
                'confidence': confidence,
                'score': score,
                'signals': signals,
                'metrics': {
                    'revenue_growth': revenue_growth,
                    'forward_pe': forward_pe,
                    'market_cap_b': market_cap / 1e9 if market_cap else 0,
                }
            }

        except Exception as e:
            return {'error': str(e)}


class IndianMomentumAlgorithm(BaseAlgorithm):
    """
    Indian Momentum Strategy
    - Uses VWAP (Volume Weighted Average Price) for entry
    - Uses Supertrend for trend confirmation and exit
    - Popular among Indian day traders
    - Works well for liquid Nifty stocks
    """

    def __init__(self):
        super().__init__(
            "Indian Momentum",
            "VWAP + Supertrend based momentum strategy for Indian markets"
        )
        self.vwap_period = 1  # Daily VWAP reset
        self.supertrend_period = 10
        self.supertrend_multiplier = 3.0

    def analyze(self, ticker: str, hist: pd.DataFrame = None) -> Dict:
        try:
            # Convert to NSE format if needed
            ticker = convert_to_nse_format(ticker)

            if hist is None:
                hist = yf.Ticker(ticker).history(period='3mo')

            if hist.empty or len(hist) < 50:
                return {'error': 'Insufficient data'}

            score = 0
            signals = []

            # 1. VWAP Analysis
            vwap = calculate_vwap(hist)
            current_price = hist['Close'].iloc[-1]
            current_vwap = vwap.iloc[-1]

            if not pd.isna(current_vwap):
                vwap_distance = ((current_price - current_vwap) / current_vwap) * 100

                if current_price > current_vwap:
                    score += 2
                    signals.append(f"Price above VWAP (+{vwap_distance:.2f}%)")
                else:
                    score -= 2
                    signals.append(f"Price below VWAP ({vwap_distance:.2f}%)")

                # Check VWAP slope (rising VWAP is bullish)
                if len(vwap) >= 5:
                    vwap_slope = vwap.iloc[-1] - vwap.iloc[-5]
                    if vwap_slope > 0:
                        score += 1
                        signals.append("VWAP rising (bullish)")

            # 2. Supertrend Analysis
            df_with_st = calculate_supertrend(hist, self.supertrend_period, self.supertrend_multiplier)

            # Guard against missing direction column
            current_direction = 0
            prev_direction = 0
            if 'direction' in df_with_st.columns:
                current_direction = df_with_st['direction'].iloc[-1]
                prev_direction = df_with_st['direction'].iloc[-2] if len(df_with_st) > 1 else current_direction

                if current_direction == 1:
                    score += 2
                    signals.append("Supertrend: Uptrend (BUY mode)")
                elif current_direction == -1:
                    score -= 2
                    signals.append("Supertrend: Downtrend (SELL mode)")

                # Check for trend change (crossover)
                if current_direction == 1 and prev_direction == -1:
                    score += 2
                    signals.append("Supertrend: Bullish crossover (entry signal)")
                elif current_direction == -1 and prev_direction == 1:
                    score -= 2
                    signals.append("Supertrend: Bearish crossover (exit signal)")

            # 3. Volume Confirmation (important for Indian markets)
            avg_volume = hist['Volume'].rolling(20).mean().iloc[-1]
            current_volume = hist['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

            if volume_ratio > 1.5:
                score += 1
                signals.append(f"Volume confirmation ({volume_ratio:.1f}x average)")

            # 4. CPR (Central Pivot Range) for breakout
            cpr = calculate_cpr(hist)
            if cpr:
                if current_price > cpr['tc']:
                    score += 1
                    signals.append("Price above CPR Top (breakout)")
                elif current_price < cpr['bc']:
                    score -= 1
                    signals.append("Price below CPR Bottom (breakdown)")

                # Narrow CPR indicates strong move coming
                if cpr.get('cpr_narrow', False):
                    signals.append("Narrow CPR detected (expect big move)")

            # Generate signal
            confidence = min(abs(score) / 8.0, 1.0)

            if score >= 4:
                signal = 'BUY'
            elif score <= -4:
                signal = 'SELL'
            else:
                signal = 'HOLD'

            return {
                'algorithm': self.name,
                'signal': signal,
                'confidence': confidence,
                'score': score,
                'signals': signals,
                'metrics': {
                    'current_price': round(current_price, 2),
                    'vwap': round(current_vwap, 2) if not pd.isna(current_vwap) else None,
                    'vwap_distance_pct': round(vwap_distance, 2) if not pd.isna(current_vwap) else None,
                    'volume_ratio': round(volume_ratio, 2),
                    'supertrend_direction': 'UP' if current_direction == 1 else 'DOWN' if 'current_direction' in locals() else 'N/A',
                    'cpr_tc': round(cpr.get('tc', 0), 2) if cpr else None,
                    'cpr_bc': round(cpr.get('bc', 0), 2) if cpr else None,
                }
            }

        except Exception as e:
            return {'error': str(e)}


class NiftyOptionsWriter(BaseAlgorithm):
    """
    Nifty Options Writer Strategy
    - Sells OTM (Out-of-the-Money) options on expiry day (Thursday)
    - Collects premium as theta decays
    - Popular Income strategy in Indian markets
    - Risk management with stop loss
    """

    def __init__(self):
        super().__init__(
            "Nifty Options Writer",
            "Sells OTM options on expiry day (Thursday) for premium collection"
        )
        self.max_otm_strikes = 2  # Sell max 2 strikes OTM
        self.min_premium_pct = 1.0  # Min 1% premium
        self.stop_loss_pct = 2.0  # Close at 2x premium received

    def analyze(self, ticker: str, hist: pd.DataFrame = None) -> Dict:
        try:
            # Convert to NSE format if needed
            ticker = convert_to_nse_format(ticker)

            # Check if today is expiry day (Thursday)
            if not is_expiry_day():
                return {
                    'algorithm': self.name,
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'score': 0,
                    'signals': ['Not expiry day (Thursday) - No action'],
                    'execute': False,
                    'reason': 'Options writing only on expiry day (Thursday)'
                }

            # Check if ticker is Nifty or BankNifty
            is_index = 'NIFTY' in ticker.upper() or 'BANKNIFTY' in ticker.upper()

            if not is_index:
                # For stocks, check if they are in F&O
                stock = yf.Ticker(ticker)
                options = stock.options
                if not options:
                    return {
                        'algorithm': self.name,
                        'signal': 'HOLD',
                        'confidence': 0.0,
                        'error': 'Stock not in F&O, cannot write options'
                    }

            score = 0
            signals = []

            # Get current price
            stock = yf.Ticker(ticker)
            current_price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')

            if not current_price:
                return {'error': 'Could not fetch current price'}

            # Get options chain for nearest expiry (today is expiry day)
            try:
                options = stock.options
                if not options:
                    return {'error': 'No options available'}

                # Get today's expiry or nearest
                today_str = datetime.now().strftime('%Y-%m-%d')
                expiry = None
                for exp in options:
                    if exp >= today_str:
                        expiry = exp
                        break

                if not expiry:
                    return {'error': 'No current expiry found'}

                chain = stock.option_chain(expiry)
                calls = chain.calls
                puts = chain.puts

                # Find OTM strikes
                # For CALLS: OTM means strike > current price (sell calls)
                otm_calls = calls[calls['strike'] > current_price].head(self.max_otm_strikes)
                # For PUTS: OTM means strike < current price (sell puts)
                otm_puts = puts[puts['strike'] < current_price].tail(self.max_otm_strikes)

                # Check premium viability
                viable_calls = []
                viable_puts = []

                for _, call in otm_calls.iterrows():
                    premium_pct = (call['lastPrice'] / current_price) * 100
                    if premium_pct >= self.min_premium_pct:
                        viable_calls.append({
                            'strike': call['strike'],
                            'premium': call['lastPrice'],
                            'premium_pct': premium_pct,
                            'volume': call['volume'],
                            'oi': call['openInterest']
                        })
                        score += 1
                        signals.append(f"OTM Call Strike {call['strike']}: Premium {premium_pct:.2f}%")

                for _, put in otm_puts.iterrows():
                    premium_pct = (put['lastPrice'] / current_price) * 100
                    if premium_pct >= self.min_premium_pct:
                        viable_puts.append({
                            'strike': put['strike'],
                            'premium': put['lastPrice'],
                            'premium_pct': premium_pct,
                            'volume': put['volume'],
                            'oi': put['openInterest']
                        })
                        score += 1
                        signals.append(f"OTM Put Strike {put['strike']}: Premium {premium_pct:.2f}%")

                # Market sentiment check
                # If market is volatile, avoid writing options
                if hist is not None and len(hist) >= 20:
                    daily_returns = hist['Close'].pct_change().dropna()
                    volatility = daily_returns.std() * np.sqrt(252)  # Annualized

                    if volatility > 0.30:  # High volatility
                        score -= 2
                        signals.append(f"High volatility ({volatility:.1%}) - Risky for options writing")
                    else:
                        signals.append(f"Volatility OK ({volatility:.1%})")

                # Generate signal
                if viable_calls or viable_puts:
                    signal = 'SELL'  # Selling/writing options
                    confidence = min(score / 4.0, 1.0)
                    execute = True
                else:
                    signal = 'HOLD'
                    confidence = 0.0
                    execute = False

                return {
                    'algorithm': self.name,
                    'signal': signal,
                    'confidence': confidence,
                    'score': score,
                    'signals': signals,
                    'execute': execute,
                    'expiry': expiry,
                    'current_price': current_price,
                    'otm_calls': viable_calls,
                    'otm_puts': viable_puts,
                    'strategy': 'SELL OTM OPTIONS ON EXPIRY',
                    'max_loss': 'Unlimited (naked write)' if signal == 'SELL' else 'None',
                    'warning': 'Use defined risk strategies (spreads) to limit risk' if signal == 'SELL' else None
                }

            except Exception as e:
                return {'error': f'Options chain error: {str(e)}'}

        except Exception as e:
            return {'error': str(e)}


class BudgetDayStrategy(BaseAlgorithm):
    """
    Budget Day Special Strategy
    - Special handling for Budget day (February 1st)
    - Market is highly volatile on Budget day
    - Avoids large positions, uses hedging
    - Focuses on sector-specific plays based on budget expectations
    """

    def __init__(self):
        super().__init__(
            "Budget Day Strategy",
            "Special strategy for Budget day (Feb 1st) with reduced risk"
        )
        self.position_size_reduction = 0.5  # Reduce position size by 50%
        self.stop_loss_tight_pct = 1.0  # Tight 1% stop loss
        self.avoid_sectors = ['oil_gas', 'banking', 'infrastructure']  # Sensitive to budget

    def analyze(self, ticker: str, hist: pd.DataFrame = None) -> Dict:
        try:
            # Convert to NSE format if needed
            ticker = convert_to_nse_format(ticker)

            # Check if today is Budget day
            budget_day = is_budget_day()

            if not budget_day:
                # Normal analysis with standard strategy
                return self._normal_analysis(ticker, hist)

            # Budget day special handling
            score = 0
            signals = []

            # Get stock info
            stock = yf.Ticker(ticker)
            info = stock.info

            sector = info.get('sector', '').lower()
            industry = info.get('industry', '').lower()

            # Check if sector is budget-sensitive
            budget_sensitive = any(s in sector or s in industry for s in self.avoid_sectors)

            if budget_sensitive:
                score -= 2
                signals.append(f"Budget-sensitive sector ({sector}) - high volatility expected")
                signals.append("Reduce position size by 50%")

            # On Budget day, prefer:
            # 1. Defensive stocks (FMCG, Pharma)
            defensive_sectors = ['consumer defensive', 'healthcare', 'pharmaceuticals']
            if any(s in sector for s in defensive_sectors):
                score += 2
                signals.append("Defensive sector - more stable on Budget day")

            # 2. Stocks with low volatility
            if hist is not None and len(hist) >= 20:
                daily_returns = hist['Close'].pct_change().dropna()
                volatility = daily_returns.std() * np.sqrt(252)

                if volatility < 0.20:
                    score += 1
                    signals.append(f"Low volatility stock ({volatility:.1%}) - safer for Budget day")
                else:
                    score -= 1
                    signals.append(f"High volatility ({volatility:.1%}) - risky for Budget day")

            # 3. Avoid aggressive entries - use tight stops
            signals.append(f"Use tight stop loss ({self.stop_loss_tight_pct}%)")
            signals.append(f"Reduce position size to {self.position_size_reduction*100}%")

            # Check for pre-budget positioning
            # Usually markets rally before budget if expectations are positive
            if hist is not None and len(hist) >= 5:
                pre_budget_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[-5] - 1) * 100
                if pre_budget_return > 2:
                    signals.append(f"Pre-budget rally (+{pre_budget_return:.1f}%) - book profits")
                    score -= 1
                elif pre_budget_return < -2:
                    signals.append(f"Pre-budget selloff ({pre_budget_return:.1f}%) - avoid fresh entries")
                    score -= 2

            # Generate signal (more conservative on Budget day)
            confidence = min(abs(score) / 6.0, 1.0)

            if score >= 2:
                signal = 'BUY'
                signals.append("BUDGET DAY: Small position BUY (50% size)")
            elif score <= -2:
                signal = 'SELL'
                signals.append("BUDGET DAY: SELL/avoid (high volatility)")
            else:
                signal = 'HOLD'
                signals.append("BUDGET DAY: HOLD - avoid new positions")

            return {
                'algorithm': self.name,
                'signal': signal,
                'confidence': confidence,
                'score': score,
                'signals': signals,
                'is_budget_day': True,
                'position_size_multiplier': self.position_size_reduction,
                'stop_loss_pct': self.stop_loss_tight_pct,
                'recommendation': 'Avoid large positions. Use hedging. Book profits early.',
                'volatile_sectors': ['Banking', 'Oil & Gas', 'Infrastructure', 'Realty'],
                'stable_sectors': ['FMCG', 'Pharma', 'IT']
            }

        except Exception as e:
            return {'error': str(e)}

    def _normal_analysis(self, ticker: str, hist: pd.DataFrame = None) -> Dict:
        """Normal analysis for non-Budget days"""
        try:
            if hist is None:
                hist = yf.Ticker(ticker).history(period='3mo')

            if hist.empty or len(hist) < 20:
                return {'error': 'Insufficient data'}

            # Simple momentum analysis
            ma_20 = hist['Close'].rolling(20).mean().iloc[-1]
            current = hist['Close'].iloc[-1]

            if current > ma_20:
                signal = 'BUY'
                score = 2
            else:
                signal = 'HOLD'
                score = 0

            return {
                'algorithm': self.name,
                'signal': signal,
                'confidence': 0.5,
                'score': score,
                'signals': ['Normal day - standard strategy'],
                'is_budget_day': False
            }
        except Exception as e:
            return {'error': str(e)}


class AlgorithmSelector:
    """
    Automatically selects the best algorithm based on market conditions
    Uses sentiment, volatility, and trend analysis
    Supports both US and Indian markets
    """

    def __init__(self, market: str = 'US'):
        """
        Initialize AlgorithmSelector
        market: 'US' for US markets, 'IN' for Indian markets
        """
        self.market = market.upper()

        # Common algorithms
        self.algorithms = {
            'buffett_value': BuffettValueAlgorithm(),
            'dalio_all_weather': DalioAllWeatherAlgorithm(),
            'bulls_ai_momentum': BullsAIStyleAlgorithm(),
            'wood_growth': WoodDisruptiveGrowthAlgorithm(),
        }

        # Add Indian-specific algorithms if market is IN
        if self.market == 'IN':
            self.algorithms['indian_momentum'] = IndianMomentumAlgorithm()
            self.algorithms['nifty_options_writer'] = NiftyOptionsWriter()
            self.algorithms['budget_day'] = BudgetDayStrategy()

    def get_market_regime(self, ticker: str = None) -> str:
        """
        Determine current market regime
        For Indian markets, uses Nifty 50 index
        """
        try:
            # Use appropriate index based on market
            if self.market == 'IN':
                # Use Nifty 50 for Indian market regime
                index_symbol = '^NSEI'  # Nifty 50
            else:
                # Use S&P 500 for US market
                index_symbol = 'SPY'

            index_data = yf.Ticker(index_symbol).history(period='6mo')

            if index_data.empty or len(index_data) < 20:
                return 'UNKNOWN'

            # Calculate trend
            ma_50 = index_data['Close'].rolling(50).mean().iloc[-1]
            ma_200 = index_data['Close'].rolling(200).mean().iloc[-1] if len(index_data) >= 200 else ma_50
            current = index_data['Close'].iloc[-1]

            # Volatility (using index)
            returns = index_data['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)

            # Determine regime
            if current > ma_50 > ma_200 and volatility < 0.20:
                return 'BULL_LOW_VOL'
            elif current > ma_50 > ma_200:
                return 'BULL_HIGH_VOL'
            elif current < ma_50 < ma_200:
                return 'BEAR'
            elif volatility > 0.30:
                return 'CRISIS'
            else:
                return 'NEUTRAL'

        except:
            return 'UNKNOWN'

    def recommend_algorithm(self, ticker: str, market_regime: str = None) -> Dict:
        """
        Recommend the best algorithm for current conditions
        """
        if market_regime is None:
            market_regime = self.get_market_regime(ticker)

        # Algorithm preference by regime (US markets)
        regime_preferences = {
            'BULL_LOW_VOL': ['bulls_ai_momentum', 'wood_growth', 'buffett_value', 'dalio_all_weather'],
            'BULL_HIGH_VOL': ['dalio_all_weather', 'buffett_value', 'bulls_ai_momentum', 'wood_growth'],
            'BEAR': ['dalio_all_weather', 'buffett_value', 'bulls_ai_momentum'],
            'CRISIS': ['dalio_all_weather', 'buffett_value'],
            'NEUTRAL': ['buffett_value', 'dalio_all_weather', 'bulls_ai_momentum'],
            'UNKNOWN': ['dalio_all_weather', 'buffett_value'],
        }

        # Add Indian algorithm preferences if market is IN
        if self.market == 'IN':
            # Add Indian algorithms to preferences
            for regime in regime_preferences:
                regime_preferences[regime].append('indian_momentum')

            # Special handling for expiry day (Thursday)
            if is_expiry_day():
                regime_preferences['NEUTRAL'].insert(0, 'nifty_options_writer')

            # Special handling for Budget day (Feb 1st)
            if is_budget_day():
                regime_preferences['NEUTRAL'].insert(0, 'budget_day')

        preferences = regime_preferences.get(market_regime, list(self.algorithms.keys()))

        # Test each preferred algorithm
        hist = yf.Ticker(ticker).history(period='6mo')

        results = []
        for algo_name in preferences:
            algo = self.algorithms[algo_name]
            result = algo.analyze(ticker, hist)

            if 'error' not in result:
                results.append({
                    'algorithm': algo_name,
                    'result': result,
                    'priority': preferences.index(algo_name)
                })

        # Sort by priority (preference) then by confidence
        results.sort(key=lambda x: (x['priority'], -x['result']['confidence']))

        if results:
            best = results[0]
            return {
                'recommended_algorithm': best['algorithm'],
                'market_regime': market_regime,
                'signal': best['result']['signal'],
                'confidence': best['result']['confidence'],
                'reasoning': f"Best suited for {market_regime} market conditions",
                'all_results': {r['algorithm']: r['result'] for r in results}
            }

        return {'error': 'No algorithm produced valid results'}

    def run_all_algorithms(self, ticker: str) -> Dict:
        """Run all algorithms and return combined signal"""
        hist = yf.Ticker(ticker).history(period='6mo')

        results = {}
        buy_score = 0
        sell_score = 0

        for name, algo in self.algorithms.items():
            result = algo.analyze(ticker, hist)
            if 'error' not in result:
                results[name] = result

                if result['signal'] == 'BUY':
                    buy_score += result['confidence']
                elif result['signal'] == 'SELL':
                    sell_score += result['confidence']

        # Combined signal
        if buy_score > sell_score * 1.5:
            combined_signal = 'BUY'
            confidence = buy_score / len(results)
        elif sell_score > buy_score * 1.5:
            combined_signal = 'SELL'
            confidence = sell_score / len(results)
        else:
            combined_signal = 'HOLD'
            confidence = 0.5

        return {
            'ticker': ticker,
            'combined_signal': combined_signal,
            'confidence': min(confidence, 1.0),
            'buy_score': round(buy_score, 2),
            'sell_score': round(sell_score, 2),
            'algorithm_results': results,
            'market_regime': self.get_market_regime()
        }
