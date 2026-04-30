"""
SmartTrader Configuration
All settings for the trading analysis system
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
MEMORY_DIR = BASE_DIR / "memory"
STRATEGIES_DIR = BASE_DIR / "strategies"
UTILS_DIR = BASE_DIR / "utils"

# Create directories
for d in [DATA_DIR, MODELS_DIR, OUTPUT_DIR, LOGS_DIR, MEMORY_DIR, STRATEGIES_DIR, UTILS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# API Keys (from environment)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "SmartTrader/1.0")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "")

# Trading Settings
MAX_TICKERS_TO_ANALYZE = int(os.getenv("MAX_TICKERS_TO_ANALYZE", "10"))
CONFIDENCE_THRESHOLD = 0.70  # 70% confidence for signals
INITIAL_CAPITAL = 100000.0  # Paper trading capital
MAX_POSITION_PCT = 0.10  # Max 10% per position
TRANSACTION_COST_BPS = 10  # 10 basis points per trade

# Data Settings
CACHE_DAYS = int(os.getenv("CACHE_DAYS", "30"))
LOOKBACK_DAYS = 252  # 1 year of trading data
NEWS_LOOKBACK_DAYS = 7  # Days to look back for news
NEWS_LIMIT_PER_SOURCE = 50

# Screener Settings - Focus on quality setups
SCREEN_CRITERIA = {
    "min_market_cap": 1e9,  # $1B minimum
    "min_avg_volume": 500000,  # 500k daily volume
    "sectors": [  # Focus on these sectors
        "Technology", "Healthcare", "Consumer Cyclical",
        "Communication Services", "Financial Services"
    ],
    "min_rsi": 30,  # Not oversold
    "max_rsi": 70,  # Not overbought
}

# ML Model Settings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, lightweight
SENTIMENT_MODEL = "distilBART"  # For summaries

# Memory Settings
MEMORY_FILE = MEMORY_DIR / "prediction_memory.json"
OUTCOMES_FILE = MEMORY_DIR / "prediction_outcomes.json"
MAX_MEMORY_ENTRIES = 10000

# Backtesting Settings
BACKTEST_INITIAL_CAPITAL = 100000.0
BACKTEST_COMMISSION_RATE = 0.001  # 0.1%
BACKTEST_SLIPPAGE = 0.001  # 0.1%

# Options Settings
OPTIONS_MIN_VOLUME = 100
OPTIONS_MIN_OPEN_INTEREST = 500
UNUSUAL_OPTIONS_VOLUME_MULTIPLIER = 3.0  # 3x average volume

# Futures Settings
FUTURES_CONTRACTS = {
    "ES": "E-mini S&P 500",
    "NQ": "E-mini NASDAQ-100",
    "CL": "Crude Oil",
    "GC": "Gold",
    "ZN": "10-Year Treasury Note",
}

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "smart_trader.log"

# Watchlist - Start with promising tickers
DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "BRK.B", "V", "JNJ"
]

# Predefined screeners for different strategies
STRATEGY_SCREENERS = {
    "momentum": {
        "min_price_change_1m": 0.05,  # 5% up in month
        "min_rsi": 50,
        "volume_surge": 1.5,  # 1.5x average volume
    },
    "value": {
        "max_pe_ratio": 20,
        "min_dividend_yield": 0.02,
        "min_roe": 0.15,
    },
    "growth": {
        "min_revenue_growth": 0.20,  # 20% growth
        "min_eps_growth": 0.25,
        "min_profit_margin": 0.15,
    },
    "swing": {
        "min_atr_pct": 0.02,  # 2% ATR
        "trending": True,
    }
}

# Risk Management
MAX_DRAWDOWN_PCT = 0.20  # 20% max drawdown
STOP_LOSS_ATR_MULTIPLIER = 2.0
TAKE_PROFIT_RR_RATIO = 2.0  # 2:1 reward:risk
