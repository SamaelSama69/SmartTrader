"""
Playground Helpers - Utility functions for the Strategy Playground
"""

import numpy as np
import pandas as pd


def format_inr(value):
    """Format value as INR"""
    if value >= 10000000:  # Crores
        return f"₹{value/10000000:.2f} Cr"
    elif value >= 100000:  # Lakhs
        return f"₹{value/100000:.2f} L"
    else:
        return f"₹{value:,.22f}"


def calculate_sharpe_ratio(returns, risk_free_rate=0.05):
    """Calculate Sharpe Ratio"""
    if len(returns) < 2:
        return 0.0
    excess_returns = returns - risk_free_rate / 252
    return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252) if np.std(excess_returns) > 0 else 0.0


def calculate_sortino_ratio(returns, risk_free_rate=0.05):
    """Calculate Sortino Ratio (only downside deviation)"""
    if len(returns) < 2:
        return 0.0
    excess_returns = returns - risk_free_rate / 252
    downside_returns = excess_returns[excess_returns < 0]
    downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0.001
    return np.mean(excess_returns) / downside_std * np.sqrt(252) if downside_std > 0 else 0.0


def calculate_max_drawdown(equity_curve):
    """Calculate Maximum Drawdown"""
    if len(equity_curve) < 2:
        return 0.0
    peak = equity_curve.expanding().max()
    drawdown = (equity_curve - peak) / peak * 100
    return abs(drawdown.min())


def calculate_calmar_ratio(returns, max_drawdown):
    """Calculate Calmar Ratio"""
    if max_drawdown == 0:
        return 0.0
    annual_return = np.mean(returns) * 252
    return annual_return / (max_drawdown / 100)


def calculate_profit_factor(trades):
    """Calculate Profit Factor (gross profits / gross losses)"""
    if not trades:
        return 0.0
    # Only consider SELL trades which have 'profit' key
    sell_trades = [t for t in trades if t.get('type') == 'SELL' and 'profit' in t]
    if not sell_trades:
        return 0.0
    profits = sum(t['profit'] for t in sell_trades if t['profit'] > 0)
    losses = abs(sum(t['profit'] for t in sell_trades if t['profit'] < 0))
    return profits / losses if losses > 0 else (profits if profits > 0 else 0.0)
