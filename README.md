# SmartTrader - AI-Powered Trading Analysis System

![Indian Markets Supported](https://img.shields.io/badge/Indian%20Markets-NSE%2FBSE%20Supported-green)

A comprehensive trading analysis system that combines sentiment analysis, technical indicators, and machine learning to identify profitable trading opportunities across stocks, options, and futures. Supports global markets and Indian markets (NSE/BSE) with Zerodha integration.

## Features

- **Multi-Source Sentiment Analysis**: News, social media (Reddit), and market sentiment
- **Smart Stock Screener**: Identifies top opportunities to focus compute on few promising companies
- **Persistent Memory System**: Records all predictions and outcomes for continuous learning
- **Backtesting Engine**: Test strategies against historical data
- **Options Analysis**: Options flow, unusual activity, and strategy Recommendations
- **Futures Analysis**: Commodities, indices, and futures spread analysis
- **Free Data Sources**: Uses yfinance, News API, Reddit API, Finnhub (free tiers)

## Quick Start

### Global Markets
```bash
cd SmartTrader
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Configure your API keys in config.py or .env file
# Free APIs: News API, Reddit API, Finnhub

python main.py --mode screen          # Find top opportunities
python main.py --mode analyze --ticker AAPL  # Analyze a stock
python main.py --mode backtest --strategy momentum  # Run backtest
python main.py --mode watch           # Start live monitoring
```

### Quick Start for Indian Users
```bash
cd SmartTrader
python -m venv venv
venv\Scripts\activate  # Windows
pip install streamlit pandas yfinance plotly requests python-dotenv

# Configure Zerodha API keys in .env file
# Get keys from: https://kite.zerodha.com/api

# Run the interactive dashboard
streamlit run dashboard.py
# Or via: python -m streamlit run dashboard.py
```

**Indian Market Hours**: 9:15 AM - 3:30 PM IST (Mon-Fri)

## Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)**: Step-by-step Windows setup, API keys, troubleshooting
- **[USAGE.md](USAGE.md)**: Complete usage documentation on:
  - Setup and configuration
  - All trading strategies
  - Options and futures tools
  - Memory system usage
  - API keys setup
  - Backtesting guide
- **[INDIAN_TRADING_GUIDE.md](INDIAN_TRADING_GUIDE.md)**: Zerodha API setup, Indian market hours, F&O, Thursday expiry, budget day trading
- **[AUTO_TRADING_GUIDE.md](AUTO_TRADING_GUIDE.md)**: One-click trading, risk management, broker connections, safety features

## Project Structure

```
SmartTrader/
├── main.py                 # Main orchestrator
├── config.py               # Configuration and API keys
├── requirements.txt        # Dependencies
├── USAGE.md              # Complete usage documentation
├── data/                  # Historical data storage
├── models/                # Trained models
├── output/                # Analysis results and charts
├── logs/                  # System logs
├── memory/                # Prediction memory and outcomes
├── strategies/            # Trading strategy modules
│   ├── stocks.py
│   ├── options.py
│   └── futures.py
└── utils/                 # Utility modules
    ├── data_fetcher.py
    ├── sentiment.py
    ├── screener.py
    ├── memory_manager.py
    ├── backtester.py
    └── visualizer.py
```

## Free APIs Used

- **yfinance**: Stock prices, options chains, fundamentals
- **News API**: Global news sentiment (free: 100 requests/day)
- **Reddit API**: Social sentiment from r/wallstreetbets, r/investing
- **Finnhub**: News and basic sentiment (free: 60 calls/min)
- **Yahoo Finance Scraping**: Additional market data

## Disclaimer

This software is for educational and research purposes. Always do your own research before making investment decisions. Past performance does not guarantee future results.
