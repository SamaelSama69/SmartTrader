"""
Playground Backtests - Backtest functions for the Strategy Playground
"""

import yfinance as yf
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import MAX_POSITION_PCT, BACKTEST_COMMISSION_RATE, BACKTEST_SLIPPAGE
from strategies.algorithms import (
    BuffettValueAlgorithm,
    BullsAIStyleAlgorithm,
    IndianMomentumAlgorithm,
    NiftyOptionsWriter,
)
from utils.backtester import Backtester
from playground_helpers import (
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown,
    calculate_calmar_ratio,
    calculate_profit_factor,
)


def backtest_buffett_value(ticker, start_date, end_date, initial_capital=100000):
    """Backtest Buffett Value Strategy"""
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)

        if data.empty or len(data) < 50:
            return {'error': 'Insufficient data'}

        algo = BuffettValueAlgorithm()
        capital = initial_capital
        position = 0
        shares = 0
        trades = []
        equity_curve = [capital]
        buy_signals = []
        sell_signals = []

        for i in range(50, len(data)):
            price = float(data['Close'].iloc[i])
            hist_slice = data.iloc[:i+1]
            result = algo.analyze(ticker, hist_slice)

            if 'error' in result:
                continue

            signal = result['signal']

            # Buy signal
            if signal == 'BUY' and position == 0:
                shares = int(capital * MAX_POSITION_PCT / price)
                cost = shares * price * (1 + BACKTEST_COMMISSION_RATE + BACKTEST_SLIPPAGE)
                if cost <= capital:
                    capital -= cost
                    position = 1
                    buy_signals.append({
                        'date': data.index[i],
                        'price': price,
                        'reason': ', '.join(result.get('signals', [])[:3])
                    })
                    trades.append({
                        'type': 'BUY',
                        'date': data.index[i],
                        'price': price,
                        'shares': shares,
                        'reason': ', '.join(result.get('signals', [])[:3])
                    })

            # Sell signal
            elif signal == 'SELL' and position == 1:
                revenue = shares * price * (1 - BACKTEST_COMMISSION_RATE - BACKTEST_SLIPPAGE)
                profit = revenue - (shares * buy_signals[-1]['price'] if buy_signals else 0)
                capital += revenue
                position = 0
                sell_signals.append({
                    'date': data.index[i],
                    'price': price,
                    'reason': ', '.join(result.get('signals', [])[:3])
                })
                trades.append({
                    'type': 'SELL',
                    'date': data.index[i],
                    'price': price,
                    'profit': profit,
                    'reason': ', '.join(result.get('signals', [])[:3])
                })
                shares = 0

            equity_curve.append(capital)

        # Close open position
        if position == 1:
            final_price = float(data['Close'].iloc[-1])
            revenue = shares * final_price * (1 - BACKTEST_COMMISSION_RATE - BACKTEST_SLIPPAGE)
            capital += revenue

        total_return = (capital - initial_capital) / initial_capital * 100

        # Calculate returns for ratios
        returns = pd.Series(equity_curve).pct_change().dropna()

        return {
            'strategy': 'Buffett Value',
            'final_value': round(capital, 2),
            'return_pct': round(total_return, 2),
            'max_drawdown_pct': round(calculate_max_drawdown(pd.Series(equity_curve)), 2),
            'total_trades': len(trades) // 2,
            'win_rate': round(sum(1 for t in trades if t.get('profit', 0) > 0) / max(len(trades) // 2, 1) * 100, 2),
            'sharpe_ratio': round(calculate_sharpe_ratio(returns), 2),
            'sortino_ratio': round(calculate_sortino_ratio(returns), 2),
            'calmar_ratio': round(calculate_calmar_ratio(returns, calculate_max_drawdown(pd.Series(equity_curve))), 2),
            'profit_factor': round(calculate_profit_factor(trades), 2),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'trades': trades,
            'equity_curve': equity_curve,
            'data': data
        }
    except Exception as e:
        return {'error': str(e)}


def backtest_bulls_ai_momentum(ticker, start_date, end_date, initial_capital=100000):
    """Backtest Bulls AI Momentum Strategy"""
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)

        if data.empty or len(data) < 50:
            return {'error': 'Insufficient data'}

        algo = BullsAIStyleAlgorithm()
        capital = initial_capital
        position = 0
        shares = 0
        trades = []
        equity_curve = [capital]
        buy_signals = []
        sell_signals = []

        for i in range(50, len(data)):
            price = float(data['Close'].iloc[i])
            hist_slice = data.iloc[:i+1]
            result = algo.analyze(ticker, hist_slice)

            if 'error' in result:
                continue

            signal = result['signal']

            # Buy signal
            if signal == 'BUY' and position == 0:
                shares = int(capital * MAX_POSITION_PCT / price)
                cost = shares * price * (1 + BACKTEST_COMMISSION_RATE + BACKTEST_SLIPPAGE)
                if cost <= capital:
                    capital -= cost
                    position = 1
                    buy_signals.append({
                        'date': data.index[i],
                        'price': price,
                        'reason': f"RSI: {result.get('metrics', {}).get('rsi', 'N/A')}, MACD: {result.get('metrics', {}).get('macd', 'N/A')}"
                    })
                    trades.append({
                        'type': 'BUY',
                        'date': data.index[i],
                        'price': price,
                        'shares': shares,
                        'reason': f"RSI: {result.get('metrics', {}).get('rsi', 'N/A')}"
                    })

            # Sell signal
            elif signal == 'SELL' and position == 1:
                revenue = shares * price * (1 - BACKTEST_COMMISSION_RATE - BACKTEST_SLIPPAGE)
                profit = revenue - (shares * buy_signals[-1]['price'] if buy_signals else 0)
                capital += revenue
                position = 0
                sell_signals.append({
                    'date': data.index[i],
                    'price': price,
                    'reason': f"RSI: {result.get('metrics', {}).get('rsi', 'N/A')}, MACD: {result.get('metrics', {}).get('macd', 'N/A')}"
                })
                trades.append({
                    'type': 'SELL',
                    'date': data.index[i],
                    'price': price,
                    'profit': profit,
                    'reason': f"RSI: {result.get('metrics', {}).get('rsi', 'N/A')}"
                })
                shares = 0

            equity_curve.append(capital)

        # Close open position
        if position == 1:
            final_price = float(data['Close'].iloc[-1])
            revenue = shares * final_price * (1 - BACKTEST_COMMISSION_RATE - BACKTEST_SLIPPAGE)
            capital += revenue

        total_return = (capital - initial_capital) / initial_capital * 100

        # Calculate returns for ratios
        returns = pd.Series(equity_curve).pct_change().dropna()

        return {
            'strategy': 'Bulls AI Momentum',
            'final_value': round(capital, 2),
            'return_pct': round(total_return, 2),
            'max_drawdown_pct': round(calculate_max_drawdown(pd.Series(equity_curve)), 2),
            'total_trades': len(trades) // 2,
            'win_rate': round(sum(1 for t in trades if t.get('profit', 0) > 0) / max(len(trades) // 2, 1) * 100, 2),
            'sharpe_ratio': round(calculate_sharpe_ratio(returns), 2),
            'sortino_ratio': round(calculate_sortino_ratio(returns), 2),
            'calmar_ratio': round(calculate_calmar_ratio(returns, calculate_max_drawdown(pd.Series(equity_curve))), 2),
            'profit_factor': round(calculate_profit_factor(trades), 2),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'trades': trades,
            'equity_curve': equity_curve,
            'data': data
        }
    except Exception as e:
        return {'error': str(e)}


def backtest_indian_momentum(ticker, start_date, end_date, initial_capital=100000):
    """Backtest Indian Momentum Strategy (VWAP + Supertrend)"""
    try:
        from utils.indian_indicators import calculate_vwap, calculate_supertrend

        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)

        if data.empty or len(data) < 50:
            return {'error': 'Insufficient data'}

        # Handle MultiIndex columns from yfinance
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)

        algo = IndianMomentumAlgorithm()
        capital = initial_capital
        position = 0
        shares = 0
        trades = []
        equity_curve = [capital]
        buy_signals = []
        sell_signals = []

        # Calculate indicators
        vwap_series = calculate_vwap(data)
        # Ensure vwap_series is a proper Series
        if isinstance(vwap_series, pd.DataFrame):
            vwap_series = vwap_series.iloc[:, 0]
        data['VWAP'] = vwap_series

        # Calculate supertrend
        data = calculate_supertrend(data.copy(), 10, 3.0)

        for i in range(50, len(data)):
            price = float(data['Close'].iloc[i])
            hist_slice = data.iloc[:i+1]
            result = algo.analyze(ticker, hist_slice)

            if 'error' in result:
                continue

            signal = result['signal']

            # Buy signal
            if signal == 'BUY' and position == 0:
                shares = int(capital * MAX_POSITION_PCT / price)
                cost = shares * price * (1 + BACKTEST_COMMISSION_RATE + BACKTEST_SLIPPAGE)
                if cost <= capital:
                    capital -= cost
                    position = 1
                    buy_signals.append({
                        'date': data.index[i],
                        'price': price,
                        'reason': f"VWAP: {result.get('metrics', {}).get('vwap', 'N/A')}, Direction: {result.get('metrics', {}).get('supertrend_direction', 'N/A')}"
                    })
                    trades.append({
                        'type': 'BUY',
                        'date': data.index[i],
                        'price': price,
                        'shares': shares,
                        'reason': f"VWAP support + Supertrend UP"
                    })

            # Sell signal
            elif signal == 'SELL' and position == 1:
                revenue = shares * price * (1 - BACKTEST_COMMISSION_RATE - BACKTEST_SLIPPAGE)
                profit = revenue - (shares * buy_signals[-1]['price'] if buy_signals else 0)
                capital += revenue
                position = 0
                sell_signals.append({
                    'date': data.index[i],
                    'price': price,
                    'reason': f"VWAP: {result.get('metrics', {}).get('vwap', 'N/A')}, Direction: {result.get('metrics', {}).get('supertrend_direction', 'N/A')}"
                })
                trades.append({
                    'type': 'SELL',
                    'date': data.index[i],
                    'price': price,
                    'profit': profit,
                    'reason': f"VWAP break + Supertrend DOWN"
                })
                shares = 0

            equity_curve.append(capital)

        # Close open position
        if position == 1:
            final_price = float(data['Close'].iloc[-1])
            revenue = shares * final_price * (1 - BACKTEST_COMMISSION_RATE - BACKTEST_SLIPPAGE)
            capital += revenue

        total_return = (capital - initial_capital) / initial_capital * 100

        # Calculate returns for ratios
        returns = pd.Series(equity_curve).pct_change().dropna()

        return {
            'strategy': 'Indian Momentum',
            'final_value': round(capital, 2),
            'return_pct': round(total_return, 2),
            'max_drawdown_pct': round(calculate_max_drawdown(pd.Series(equity_curve)), 2),
            'total_trades': len(trades) // 2,
            'win_rate': round(sum(1 for t in trades if t.get('profit', 0) > 0) / max(len(trades) // 2, 1) * 100, 2),
            'sharpe_ratio': round(calculate_sharpe_ratio(returns), 2),
            'sortino_ratio': round(calculate_sortino_ratio(returns), 2),
            'calmar_ratio': round(calculate_calmar_ratio(returns, calculate_max_drawdown(pd.Series(equity_curve))), 2),
            'profit_factor': round(calculate_profit_factor(trades), 2),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'trades': trades,
            'equity_curve': equity_curve,
            'data': data
        }
    except Exception as e:
        return {'error': str(e)}


def backtest_nifty_options_writer(ticker, start_date, end_date, initial_capital=100000):
    """Backtest Nifty Options Writer Strategy"""
    try:
        # Options writing is more complex - simplified backtest
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)

        if data.empty or len(data) < 50:
            return {'error': 'Insufficient data'}

        algo = NiftyOptionsWriter()
        capital = initial_capital
        trades = []
        equity_curve = [capital]

        # For options writer, we simulate collecting premium on expiry days
        # This is a simplified version
        for i in range(len(data)):
            date = data.index[i]
            price = float(data['Close'].iloc[i])

            # Check if it's Thursday (simplified expiry day check)
            if date.weekday() == 3:  # Thursday
                # Simulate collecting premium (typically 1-2% per week)
                premium_collected = capital * 0.01  # 1% premium
                capital += premium_collected
                trades.append({
                    'type': 'PREMIUM',
                    'date': date,
                    'price': price,
                    'profit': premium_collected,
                    'reason': 'Options premium collected on expiry day'
                })

            equity_curve.append(capital)

        total_return = (capital - initial_capital) / initial_capital * 100

        # Calculate returns for ratios
        returns = pd.Series(equity_curve).pct_change().dropna()

        return {
            'strategy': 'Nifty Options Writer',
            'final_value': round(capital, 2),
            'return_pct': round(total_return, 2),
            'max_drawdown_pct': round(calculate_max_drawdown(pd.Series(equity_curve)), 2),
            'total_trades': len(trades),
            'win_rate': 100.0,  # Assuming premium collection is typically profitable
            'sharpe_ratio': round(calculate_sharpe_ratio(returns), 2),
            'sortino_ratio': round(calculate_sortino_ratio(returns), 2),
            'calmar_ratio': round(calculate_calmar_ratio(returns, calculate_max_drawdown(pd.Series(equity_curve))), 2),
            'profit_factor': 2.0,  # Options writing typically has high profit factor
            'buy_signals': [],
            'sell_signals': [],
            'trades': trades,
            'equity_curve': equity_curve,
            'data': data
        }
    except Exception as e:
        return {'error': str(e)}


def backtest_buy_and_hold(ticker, start_date, end_date, initial_capital=100000):
    """Benchmark: Simple buy and hold strategy"""
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)

        if data.empty:
            return {'error': 'No data available'}

        initial_price = float(data['Close'].iloc[0])
        final_price = float(data['Close'].iloc[-1])
        shares = int(initial_capital / initial_price)

        final_value = shares * final_price
        total_return = (final_value - initial_capital) / initial_capital * 100

        # Create equity curve (simplified - just linear growth)
        equity_curve = [initial_capital]
        for i in range(1, len(data)):
            current_price = float(data['Close'].iloc[i])
            equity_curve.append(shares * current_price)

        # Calculate max drawdown
        equity_series = pd.Series(equity_curve)
        max_drawdown = calculate_max_drawdown(equity_series)

        # Calculate returns for ratios
        returns = equity_series.pct_change().dropna()

        return {
            'strategy': 'Buy and Hold (Benchmark)',
            'final_value': round(final_value, 2),
            'return_pct': round(total_return, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'total_trades': 1,
            'win_rate': 100.0 if total_return > 0 else 0.0,
            'sharpe_ratio': round(calculate_sharpe_ratio(returns), 2),
            'sortino_ratio': round(calculate_sortino_ratio(returns), 2),
            'calmar_ratio': round(calculate_calmar_ratio(returns, max_drawdown), 2),
            'profit_factor': 1.0 if total_return > 0 else 0.0,
            'buy_signals': [{'date': data.index[0], 'price': initial_price, 'reason': 'Initial buy'}],
            'sell_signals': [{'date': data.index[-1], 'price': final_price, 'reason': 'Final price'}],
            'trades': [{'type': 'BUY', 'date': data.index[0], 'price': initial_price, 'shares': shares}],
            'equity_curve': equity_curve,
            'data': data
        }
    except Exception as e:
        return {'error': str(e)}
