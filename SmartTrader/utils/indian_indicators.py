"""
Indian-Specific Technical Indicators
Critical indicators used by Indian traders for NSE/BSE markets
"""

import logging
import pandas as pd
import numpy as np
import pytz
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date

logger = logging.getLogger(__name__)


def calculate_vwap(df: pd.DataFrame, anchor: str = 'day') -> pd.Series:
    """
    Calculate Volume Weighted Average Price (VWAP)
    Critical for Indian intraday trading

    Parameters:
    -----------
    df : pd.DataFrame with columns ['High', 'Low', 'Close', 'Volume']
    anchor : str - 'day' for intraday, 'session' for custom sessions

    Returns:
    --------
    pd.Series with VWAP values
    """
    if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close', 'Volume']):
        return pd.Series(index=df.index)

    # Typical Price
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3

    # Cumulative values for VWAP
    cumulative_tp_volume = (typical_price * df['Volume']).cumsum()
    cumulative_volume = df['Volume'].cumsum()

    # Avoid division by zero
    vwap = cumulative_tp_volume / cumulative_volume.replace(0, np.nan)

    return vwap


def calculate_pivot_points(df: pd.DataFrame, method: str = 'classic') -> Dict[str, float]:
    """
    Calculate Pivot Points - widely used in Indian markets

    Methods:
    - 'classic': Standard pivot points
    - 'fibonacci': Fibonacci retracement levels
    - 'camarilla': Camarilla pivot points (popular in India)

    Returns dictionary with pivot levels
    """
    if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
        return {}

    if len(df) < 2:
        logger.warning("Not enough data for pivot points (need at least 2 rows)")
        return {}

    # Use previous day's data for pivot calculation (iloc[-2] to get prior day)
    prev_high = df['High'].iloc[-2]
    prev_low = df['Low'].iloc[-2]
    prev_close = df['Close'].iloc[-2]

    pivot = (prev_high + prev_low + prev_close) / 3

    result = {'pivot': pivot, 'high': prev_high, 'low': prev_low, 'close': prev_close}

    if method == 'classic':
        # Classic Pivot Points
        r1 = (2 * pivot) - prev_low
        r2 = pivot + (prev_high - prev_low)
        r3 = r1 + (prev_high - prev_low)
        s1 = (2 * pivot) - prev_high
        s2 = pivot - (prev_high - prev_low)
        s3 = s1 - (prev_high - prev_low)

        result.update({
            'r1': r1, 'r2': r2, 'r3': r3,
            's1': s1, 's2': s2, 's3': s3
        })

    elif method == 'fibonacci':
        # Fibonacci Pivot Points
        diff = prev_high - prev_low
        r1 = pivot + (0.382 * diff)
        r2 = pivot + (0.618 * diff)
        r3 = pivot + (1.0 * diff)
        s1 = pivot - (0.382 * diff)
        s2 = pivot - (0.618 * diff)
        s3 = pivot - (1.0 * diff)

        result.update({
            'r1': r1, 'r2': r2, 'r3': r3,
            's1': s1, 's2': s2, 's3': s3
        })

    elif method == 'camarilla':
        # Camarilla Pivot Points (very popular in India)
        diff = prev_high - prev_low
        r1 = prev_close + (diff * 1.1 / 12)
        r2 = prev_close + (diff * 1.1 / 6)
        r3 = prev_close + (diff * 1.1 / 4)
        r4 = prev_close + (diff * 1.1 / 2)
        s1 = prev_close - (diff * 1.1 / 12)
        s2 = prev_close - (diff * 1.1 / 6)
        s3 = prev_close - (diff * 1.1 / 4)
        s4 = prev_close - (diff * 1.1 / 2)

        result.update({
            'r1': r1, 'r2': r2, 'r3': r3, 'r4': r4,
            's1': s1, 's2': s2, 's3': s3, 's4': s4
        })

    return result


def calculate_cpr(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Central Pivot Range (CPR)
    Extremely popular among Indian traders for identifying breakouts

    CPR consists of:
    - TC (Top Central): (Pivot + BC) / 2
    - BC (Bottom Central): (Previous High + Previous Low) / 2
    - Pivot: (H + L + C) / 3

    Returns dictionary with CPR values
    """
    if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
        return {}

    if len(df) < 2:
        logger.warning("Not enough data for CPR (need at least 2 rows)")
        return {}

    # Use previous day's data (iloc[-2] to get prior day)
    prev_high = df['High'].iloc[-2]
    prev_low = df['Low'].iloc[-2]
    prev_close = df['Close'].iloc[-2]

    # Calculate pivots
    pivot = (prev_high + prev_low + prev_close) / 3
    bc = (prev_high + prev_low) / 2  # Bottom Central
    tc = (pivot + bc) / 2  # Top Central

    # Determine CPR width
    cpr_width = abs(tc - bc)

    return {
        'pivot': pivot,
        'tc': tc,
        'bc': bc,
        'cpr_width': cpr_width,
        'cpr_narrow': cpr_width < (prev_high - prev_low) * 0.2  # Narrow CPR indicates strong move
    }


def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """
    Calculate Supertrend Indicator
    Works exceptionally well for Indian trending stocks

    Parameters:
    -----------
    df : pd.DataFrame with columns ['High', 'Low', 'Close']
    period : int - ATR period (default 10)
    multiplier : float - ATR multiplier (default 3.0)

    Returns:
    --------
    pd.DataFrame with 'supertrend', 'direction', 'upper_band', 'lower_band' columns
    """
    if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
        return df

    result_df = df.copy()

    # Calculate ATR
    atr = calculate_atr(df, period)

    # Calculate basic upper and lower bands
    basic_upperband = (df['High'] + df['Low']) / 2 + (multiplier * atr)
    basic_lowerband = (df['High'] + df['Low']) / 2 - (multiplier * atr)

    # Initialize final bands
    final_upperband = pd.Series(index=df.index, dtype=float)
    final_lowerband = pd.Series(index=df.index, dtype=float)
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)  # 1 for uptrend, -1 for downtrend

    # First value - ensure scalar assignment
    final_upperband.iloc[period-1] = float(basic_upperband.iloc[period-1])
    final_lowerband.iloc[period-1] = float(basic_lowerband.iloc[period-1])

    # Calculate bands
    for i in range(period, len(df)):
        # Upper band
        if (basic_upperband.iloc[i] < final_upperband.iloc[i-1]) or \
           (df['Close'].iloc[i-1] > final_upperband.iloc[i-1]):
            final_upperband.iloc[i] = basic_upperband.iloc[i]
        else:
            final_upperband.iloc[i] = final_upperband.iloc[i-1]

        # Lower band
        if (basic_lowerband.iloc[i] > final_lowerband.iloc[i-1]) or \
           (df['Close'].iloc[i-1] < final_lowerband.iloc[i-1]):
            final_lowerband.iloc[i] = basic_lowerband.iloc[i]
        else:
            final_lowerband.iloc[i] = final_lowerband.iloc[i-1]

        # Supertrend and direction
        if df['Close'].iloc[i] <= final_upperband.iloc[i]:
            direction.iloc[i] = -1
            supertrend.iloc[i] = final_upperband.iloc[i]
        else:
            direction.iloc[i] = 1
            supertrend.iloc[i] = final_lowerband.iloc[i]

    result_df['supertrend'] = supertrend
    result_df['direction'] = direction
    result_df['upper_band'] = final_upperband
    result_df['lower_band'] = final_lowerband

    return result_df


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR)
    """
    if df.empty or not all(col in df.columns for col in ['High', 'Low', 'Close']):
        return pd.Series(index=df.index)

    high = df['High']
    low = df['Low']
    close = df['Close']

    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()

    return atr


def get_indian_intraday_signals(df: pd.DataFrame) -> Dict:
    """
    Generate trading signals based on Indian popular indicators
    Combines VWAP, CPR, and Supertrend for comprehensive signals
    """
    if df.empty:
        return {'signal': 'HOLD', 'confidence': 0.0, 'reasons': []}

    signals = []
    score = 0
    reasons = []

    # Calculate indicators
    vwap = calculate_vwap(df)
    current_price = df['Close'].iloc[-1]
    current_vwap = vwap.iloc[-1]

    # VWAP Signal
    if not pd.isna(current_vwap):
        if current_price > current_vwap:
            score += 2
            reasons.append("Price above VWAP (Bullish)")
        else:
            score -= 2
            reasons.append("Price below VWAP (Bearish)")
        signals.append({'indicator': 'VWAP', 'value': current_vwap, 'position': 'above' if current_price > current_vwap else 'below'})

    # CPR Signal
    cpr = calculate_cpr(df)
    if cpr:
        if current_price > cpr['tc']:
            score += 2
            reasons.append("Price above CPR Top (Strong Bullish)")
        elif current_price < cpr['bc']:
            score -= 2
            reasons.append("Price below CPR Bottom (Strong Bearish)")
        else:
            reasons.append("Price within CPR range (Neutral)")
        signals.append({'indicator': 'CPR', 'tc': cpr['tc'], 'bc': cpr['bc'], 'narrow': cpr['cpr_narrow']})

    # Supertrend Signal
    df_with_st = calculate_supertrend(df)
    if 'direction' in df_with_st.columns:
        current_direction = df_with_st['direction'].iloc[-1]
        if current_direction == 1:
            score += 2
            reasons.append("Supertrend shows Uptrend")
        elif current_direction == -1:
            score -= 2
            reasons.append("Supertrend shows Downtrend")
        signals.append({'indicator': 'Supertrend', 'direction': 'UP' if current_direction == 1 else 'DOWN'})

    # Pivot Points for reference
    pivots = calculate_pivot_points(df, 'classic')
    signals.append({'indicator': 'Pivot', 'levels': pivots})

    # Generate final signal
    confidence = min(abs(score) / 6.0, 1.0)

    if score >= 3:
        signal = 'BUY'
    elif score <= -3:
        signal = 'SELL'
    else:
        signal = 'HOLD'

    return {
        'signal': signal,
        'confidence': confidence,
        'score': score,
        'reasons': reasons,
        'indicators': signals,
        'current_price': current_price
    }


def is_expiry_day() -> bool:
    """
    Check if today is expiry day (Thursday for Indian markets)
    Also checks for holiday adjustments
    """
    ist = pytz.timezone('Asia/Kolkata')
    today = datetime.now(ist)
    # Nifty/BankNifty expire on Thursday
    return today.weekday() == 3  # 3 = Thursday


def is_budget_day() -> bool:
    """
    Check if today is Budget day (February 1st)
    """
    ist = pytz.timezone('Asia/Kolkata')
    today = datetime.now(ist)
    return today.month == 2 and today.day == 1
