"""
NSE (National Stock Exchange) Data Fetcher
Fetches Nifty 50/500 tickers, F&O listings, and corporate actions
"""

import yfinance as yf
import pandas as pd
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, date
import json
from config import *

# Nifty 50 tickers (as of 2024, with .NS suffix for Yahoo Finance)
NIFTY_50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "HCLTECH.NS", "TITAN.NS",
    "ULTRACEMCO.NS", "WIPRO.NS", "MARUTI.NS", "NTPC.NS", "POWERGRID.NS",
    "ONGC.NS", "SUNPHARMA.NS", "TATAMOTORS.NS", "BAJAJFINSV.NS", "DRREDDY.NS",
    "ADANIPORTS.NS", "COALINDIA.NS", "BPCL.NS", "EICHERMOT.NS", "TATASTEEL.NS",
    "JSWSTEEL.NS", "HINDALCO.NS", "GRASIM.NS", "CIPLA.NS", "UPL.NS",
    "DIVISLAB.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS", "TECHM.NS", "INDUSINDBK.NS",
    "SIEMENS.NS", "SBILIFE.NS", "HDFCLIFE.NS", "M&M.NS", "BRITANNIA.NS",
    "APOLLOHOSP.NS", "PIDILITIND.NS", "DABUR.NS", "AMBUJACEM.NS", "SHRIRAMFIN.NS"
]

# Nifty 500 - Larger list for broader analysis
NIFTY_500_TICKERS = NIFTY_50_TICKERS + [
    "ACC.NS", "AUROPHARMA.NS", "BANKBARODA.NS", "BIOCON.NS", "BOSCHLTD.NS",
    "CANBK.NS", "CHOLAFIN.NS", "DALMIABHA.NS", "DLF.NS", "FEDERALBNK.NS",
    "GAIL.NS", "GLAND.NS", "GMRINFRA.NS", "GODREJCP.NS", "HAVELLS.NS",
    "HEG.NS", "IDFCFIRSTB.NS", "IGL.NS", "INDIGO.NS", "JINDALSTEL.NS",
    "JUBLFOOD.NS", "LUPIN.NS", "MFSL.NS", "MOTHERSUMI.NS", "MRF.NS",
    "NMDC.NS", "PEL.NS", "PETRONET.NS", "PFC.NS", "PNB.NS",
    "RVNL.NS", "SAIL.NS", "SRF.NS", "TATACHEM.NS", "TATAPOWER.NS",
    "TORNTPHARM.NS", "TVSMOTOR.NS", "UBL.NS", "VOLTAS.NS", "ZEEL.NS"
]

# Popular F&O Stocks (frequently traded in Futures & Options)
FNO_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "BAJFINANCE.NS", "HCLTECH.NS", "TITAN.NS",
    "MARUTI.NS", "TATAMOTORS.NS", "SUNPHARMA.NS", "DRREDDY.NS", "ADANIPORTS.NS",
    "BPCL.NS", "EICHERMOT.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS",
    "CIPLA.NS", "UPL.NS", "BAJAJ-AUTO.NS", "TECHM.NS", "INDUSINDBK.NS"
]

# Bank Nifty components
BANKNIFTY_TICKERS = [
    "HDFCBANK.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS",
    "SBIN.NS", "INDUSINDBK.NS", "BANKBARODA.NS", "FEDERALBNK.NS",
    "IDFCFIRSTB.NS", "PNB.NS", "AUROPHARMA.NS", "CIPLA.NS"
]


class NSEDataFetcher:
    """Fetch NSE-specific data for Indian markets"""

    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def get_nifty_50_tickers(self) -> List[str]:
        """Return Nifty 50 ticker list"""
        return NIFTY_50_TICKERS

    def get_nifty_500_tickers(self) -> List[str]:
        """Return Nifty 500 ticker list"""
        return NIFTY_500_TICKERS

    def get_fno_stocks(self) -> List[str]:
        """Return F&O stock list"""
        return FNO_STOCKS

    def get_banknifty_tickers(self) -> List[str]:
        """Return Bank Nifty component tickers"""
        return BANKNIFTY_TICKERS

    def get_index_data(self, index: str = "NIFTY50") -> pd.DataFrame:
        """
        Fetch index data
        index: "NIFTY50", "BANKNIFTY", "NIFTY500"
        """
        index_map = {
            "NIFTY50": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "NIFTY500": "^CRSLDX"
        }

        symbol = index_map.get(index.upper())
        if not symbol:
            return pd.DataFrame()

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="6mo")
            return df
        except Exception as e:
            print(f"Error fetching index data for {index}: {e}")
            return pd.DataFrame()

    def get_fno_lot_sizes(self) -> Dict[str, int]:
        """
        Get F&O lot sizes for popular stocks
        Note: Lot sizes are updated by SEBI periodically
        """
        return {
            "NIFTY": 50,
            "BANKNIFTY": 15,
            "FINNIFTY": 40,
            "RELIANCE": 250,
            "TCS": 175,
            "HDFCBANK": 500,
            "INFY": 600,
            "ICICIBANK": 1375,
            "HINDUNILVR": 200,
            "ITC": 3200,
            "SBIN": 1500,
            "BHARTIARTL": 2200,
            "KOTAKBANK": 625,
            "LT": 375,
            "AXISBANK": 975,
            "BAJFINANCE": 125,
            "HCLTECH": 350,
            "TITAN": 375,
            "MARUTI": 100,
            "TATAMOTORS": 3000,
            "SUNPHARMA": 750,
            "DRREDDY": 250,
            "ADANIPORTS": 1500,
            "BAJAJ-AUTO": 125,
        }

    def get_corporate_actions(self, ticker: str, days: int = 30) -> Dict:
        """
        Fetch corporate actions (dividends, bonus, splits) for a ticker
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            actions = {
                'ticker': ticker,
                'dividends': [],
                'splits': [],
                'bonus': []
            }

            # Get dividends
            try:
                dividends = stock.dividends
                if not dividends.empty:
                    recent_divs = dividends.last(f'{days}D')
                    for date, value in recent_divs.items():
                        actions['dividends'].append({
                            'date': date.strftime('%Y-%m-%d'),
                            'amount': float(value)
                        })
            except:
                pass

            # Get stock splits
            try:
                splits = stock.splits
                if not splits.empty:
                    recent_splits = splits.last(f'{days}D')
                    for date, value in recent_splits.items():
                        actions['splits'].append({
                            'date': date.strftime('%Y-%m-%d'),
                            'ratio': float(value)
                        })
            except:
                pass

            # Corporate info from info
            actions['upcoming_events'] = {
                'ex_dividend_date': info.get('exDividendDate', None),
                'dividend_rate': info.get('dividendRate', None),
                'dividend_yield': info.get('dividendYield', None),
            }

            return actions

        except Exception as e:
            print(f"Error fetching corporate actions for {ticker}: {e}")
            return {'ticker': ticker, 'error': str(e)}

    def get_options_chain_nse(self, ticker: str) -> Dict:
        """
        Fetch options chain for NSE ticker
        Returns calls and puts with relevant data
        """
        try:
            stock = yf.Ticker(ticker)
            expirations = stock.options

            if not expirations:
                return {'error': 'No options available'}

            # Get nearest expiry
            options_data = {}
            for exp in expirations[:3]:  # Limit to 3 nearest expirations
                chain = stock.option_chain(exp)
                options_data[exp] = {
                    'calls': chain.calls.to_dict('records'),
                    'puts': chain.puts.to_dict('records')
                }

            return options_data

        except Exception as e:
            return {'error': str(e)}

    def get_market_holidays(self, year: int = None) -> List[date]:
        """
        Get NSE market holidays
        (Static list - should be updated yearly from NSE website)
        """
        if year is None:
            year = datetime.now().year

        # Major NSE holidays (static - update from nseindia.com)
        holidays_2024 = [
            date(2024, 1, 26),  # Republic Day
            date(2024, 3, 8),   # Mahashivratri
            date(2024, 3, 25),  # Holi
            date(2024, 3, 29),  # Good Friday
            date(2024, 4, 11),  # Id-Ul-Fitr
            date(2024, 4, 17),  # Ram Navami
            date(2024, 5, 1),   # Maharashtra Day
            date(2024, 6, 17),  # Bakri Id
            date(2024, 7, 17),  # Moharram
            date(2024, 8, 15),  # Independence Day
            date(2024, 10, 2),  # Gandhi Jayanti
            date(2024, 11, 1),  # Diwali-Laxmi Pujan
            date(2024, 11, 15), # Gurunanak Jayanti
            date(2024, 12, 25), # Christmas
        ]

        holidays_2025 = [
            date(2025, 1, 26),  # Republic Day
            date(2025, 3, 14),  # Holi
            date(2025, 3, 29),  # Good Friday
            date(2025, 4, 1),   # Id-Ul-Fitr
            date(2025, 5, 1),   # Maharashtra Day
            date(2025, 8, 15),  # Independence Day
            date(2025, 10, 2),  # Gandhi Jayanti
            date(2025, 10, 21), # Diwali
            date(2025, 12, 25), # Christmas
        ]

        if year == 2024:
            return holidays_2024
        elif year == 2025:
            return holidays_2025
        else:
            return []

    def is_market_open(self) -> bool:
        """
        Check if NSE market is currently open
        Trading hours: 9:15 AM - 3:30 PM IST (Mon-Fri)
        """
        now = datetime.now()

        # Check if weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Check if holiday
        holidays = self.get_market_holidays(now.year)
        if now.date() in holidays:
            return False

        # Check trading hours (9:15 AM to 3:30 PM IST)
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        return market_open <= now <= market_close

    def get_popular_indian_stocks(self) -> Dict[str, List[str]]:
        """
        Return categorized popular Indian stocks for screening
        """
        return {
            'nifty_50': NIFTY_50_TICKERS,
            'fno_stocks': FNO_STOCKS,
            'bank_nifty': BANKNIFTY_TICKERS,
            'it_stocks': [
                "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS",
                "TECHM.NS", "L&TTECH.NS", "PERSISTENT.NS"
            ],
            'banking_stocks': [
                "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS",
                "AXISBANK.NS", "INDUSINDBK.NS", "FEDERALBNK.NS", "IDFCFIRSTB.NS"
            ],
            'pharma_stocks': [
                "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "LUPIN.NS",
                "BIOCON.NS", "TORNTPHARM.NS", "AUROPHARMA.NS", "DIVISLAB.NS"
            ],
            'auto_stocks': [
                "MARUTI.NS", "TATAMOTORS.NS", "BAJAJ-AUTO.NS",
                "HEROMOTOCO.NS", "EICHERMOT.NS", "TVSMOTOR.NS", "M&M.NS"
            ],
        }


def convert_to_nse_format(ticker: str) -> str:
    """
    Convert ticker to NSE format (append .NS if not present)
    Example: RELIANCE -> RELIANCE.NS
    """
    ticker = ticker.upper().strip()

    # If already has .NS suffix, return as is
    if ticker.endswith('.NS'):
        return ticker

    # If has .BO (BSE), convert to NSE
    if ticker.endswith('.BO'):
        return ticker.replace('.BO', '.NS')

    # Add .NS suffix for NSE
    return f"{ticker}.NS"


def convert_from_nse_format(ticker: str) -> str:
    """
    Remove .NS suffix from ticker for display
    Example: RELIANCE.NS -> RELIANCE
    """
    return ticker.replace('.NS', '')
