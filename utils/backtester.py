"""
Backtesting Engine - Test strategies against historical data
Uses free yfinance data for backtesting
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
import yfinance as yf
from config import *


class Backtester:
    """Backtest trading strategies on historical data"""

    def __init__(self, initial_capital: float = BACKTEST_INITIAL_CAPITAL):
        self.initial_capital = initial_capital
        self.commission_rate = BACKTEST_COMMISSION_RATE
        self.slippage = BACKTEST_SLIPPAGE

    def buy_and_hold(self, ticker: str, start_date: str, end_date: str = None) -> Dict:
        """Benchmark: Simple buy and hold strategy"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)

        if data.empty:
            return {'error': 'No data available'}

        initial_price = float(data['Close'].iloc[0].squeeze())
        final_price = float(data['Close'].iloc[-1].squeeze())
        shares = int(self.initial_capital / initial_price)

        final_value = shares * final_price
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100

        return {
            'strategy': 'buy_and_hold',
            'ticker': ticker,
            'initial_capital': self.initial_capital,
            'final_value': round(final_value, 2),
            'return_pct': round(total_return, 2),
            'shares_held': shares,
            'start_date': start_date,
            'end_date': end_date
        }

    def moving_average_crossover(self, ticker: str, start_date: str,
                                 fast_window: int = 20, slow_window: int = 50,
                                 end_date: str = None) -> Dict:
        """Moving Average Crossover Strategy"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)

        if data.empty or len(data) < slow_window:
            return {'error': 'Insufficient data'}

        # Calculate moving averages
        data['Fast_MA'] = data['Close'].rolling(fast_window).mean()
        data['Slow_MA'] = data['Close'].rolling(slow_window).mean()

        # Generate signals
        data['Signal'] = 0
        data.loc[data['Fast_MA'] > data['Slow_MA'], 'Signal'] = 1  # Buy
        data.loc[data['Fast_MA'] < data['Slow_MA'], 'Signal'] = -1  # Sell

        # Backtest
        capital = self.initial_capital
        position = 0
        shares = 0
        trades = []

        for i in range(slow_window, len(data)):
            price = float(data['Close'].iloc[i])
            signal = int(data['Signal'].iloc[i])
            prev_signal = int(data['Signal'].iloc[i-1])

            # Buy signal
            if signal == 1 and prev_signal != 1 and position == 0:
                shares = int(capital * MAX_POSITION_PCT / price)
                cost = shares * price * (1 + self.commission_rate + self.slippage)
                if cost <= capital:
                    capital -= cost
                    position = 1
                    trades.append({'type': 'BUY', 'price': price, 'shares': shares, 'date': data.index[i]})

            # Sell signal
            elif signal == -1 and position == 1:
                revenue = shares * price * (1 - self.commission_rate - self.slippage)
                capital += revenue
                position = 0
                trades.append({'type': 'SELL', 'price': price, 'shares': shares, 'date': data.index[i]})
                shares = 0

        # Close any open position
        if position == 1:
            final_price = float(data['Close'].iloc[-1])
            revenue = shares * final_price * (1 - self.commission_rate - self.slippage)
            capital += revenue
            trades.append({'type': 'CLOSE', 'price': final_price, 'shares': shares, 'date': data.index[-1]})

        total_return = (capital - self.initial_capital) / self.initial_capital * 100

        # Calculate max drawdown
        data['Cumulative_Returns'] = (data['Close'] / data['Close'].iloc[0] - 1)
        running_max = data['Cumulative_Returns'].cummax()
        drawdown = (data['Cumulative_Returns'] - running_max)
        max_drawdown = drawdown.min() * 100

        return {
            'strategy': 'ma_crossover',
            'ticker': ticker,
            'initial_capital': self.initial_capital,
            'final_value': round(capital, 2),
            'return_pct': round(total_return, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'total_trades': len(trades),
            'start_date': start_date,
            'end_date': end_date,
            'trades': trades[:10]  # First 10 trades for review
        }

    def rsi_strategy(self, ticker: str, start_date: str,
                     oversold: int = 30, overbought: int = 70,
                     end_date: str = None) -> Dict:
        """RSI Mean Reversion Strategy"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)

        if data.empty or len(data) < 20:
            return {'error': 'Insufficient data'}

        # Calculate RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # Generate signals
        capital = self.initial_capital
        position = 0
        shares = 0
        trades = []

        for i in range(14, len(data)):
            rsi = float(data['RSI'].iloc[i])
            price = float(data['Close'].iloc[i])

            # Buy when RSI oversold
            if rsi < oversold and position == 0:
                shares = int(capital * MAX_POSITION_PCT / price)
                cost = shares * price * (1 + self.commission_rate + self.slippage)
                if cost <= capital:
                    capital -= cost
                    position = 1
                    trades.append({'type': 'BUY', 'price': price, 'rsi': rsi, 'date': data.index[i]})

            # Sell when RSI overbought
            elif rsi > overbought and position == 1:
                revenue = shares * price * (1 - self.commission_rate - self.slippage)
                capital += revenue
                position = 0
                trades.append({'type': 'SELL', 'price': price, 'rsi': rsi, 'date': data.index[i]})
                shares = 0

        # Close open position
        if position == 1:
            final_price = float(data['Close'].iloc[-1])
            revenue = shares * final_price * (1 - self.commission_rate - self.slippage)
            capital += revenue

        total_return = (capital - self.initial_capital) / self.initial_capital * 100

        return {
            'strategy': 'rsi_mean_reversion',
            'ticker': ticker,
            'initial_capital': self.initial_capital,
            'final_value': round(capital, 2),
            'return_pct': round(total_return, 2),
            'total_trades': len(trades),
            'start_date': start_date,
            'end_date': end_date,
        }

    def compare_strategies(self, ticker: str, start_date: str, end_date: str = None) -> Dict:
        """Compare multiple strategies on the same ticker"""
        results = {}

        # Buy and Hold
        results['buy_hold'] = self.buy_and_hold(ticker, start_date, end_date)

        # MA Crossover
        results['ma_crossover'] = self.moving_average_crossover(ticker, start_date, end_date)

        # RSI Strategy
        results['rsi'] = self.rsi_strategy(ticker, start_date, end_date)

        # Find best strategy
        best_strategy = max(results.items(), key=lambda x: x[1].get('return_pct', -999))

        return {
            'ticker': ticker,
            'strategies': results,
            'best_strategy': best_strategy[0],
            'best_return': best_strategy[1].get('return_pct', 0)
        }
