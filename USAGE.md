# SmartTrader - Complete Usage Guide

A comprehensive guide to using the SmartTrader system for profitable trading analysis.

## Table of Contents
1. [Installation](#installation)
2. [API Keys Setup](#api-keys-setup)
3. [Quick Start](#quick-start)
4. [Command Line Usage](#command-line-usage)
5. [Interactive Dashboard](#interactive-dashboard)
6. [Trading Strategies](#trading-strategies)
7. [Expert Tracking System](#expert-tracking-system)
8. [Memory & Prediction Tracking](#memory--prediction-tracking)
9. [Backtesting](#backtesting)
10. [Options Trading](#options-trading)
11. [Futures Trading](#futures-trading)
12. [Advanced Features](#advanced-features)
13. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Steps
```bash
cd "C:\Users\Sham\Desktop\Projects\NLP SENTIMENT ANALYSIS\SmartTrader"

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note for Windows TA-Lib:**
If `ta-lib` installation fails, install via:
```bash
pip install ta-lib-windows
```

---

## API Keys Setup

Copy `.env.example` to `.env` and fill in your free API keys:

```bash
copy .env.example .env
```

### Free APIs to Register:
1. **News API** (100 requests/day free): https://newsapi.org/register
2. **Reddit API** (free, create script app): https://www.reddit.com/prefs/apps
3. **Finnhub** (60 calls/minute free): https://finnhub.io/register
4. **Alpha Vantage** (5 calls/min free, optional): https://www.alphavantage.co/support/#api-key

Edit `.env`:
```env
NEWS_API_KEY=your_news_api_key_here
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
FINNHUB_API_KEY=your_finnhub_api_key
ALPHA_VANTAGE_KEY=your_alpha_vantage_key
```

---

## Quick Start

### 1. Screen for Opportunities
```bash
python main.py --mode screen
```
This finds the top trading opportunities using free data. Results are saved to `output/screened_opportunities.json`.

### 2. Analyze a Stock
```bash
python main.py --mode analyze --ticker AAPL
```
Get full analysis with AI signal, sentiment, and technical indicators.

### 3. Launch Interactive Dashboard
```bash
streamlit run dashboard.py
```
Opens a browser with interactive charts, expert opinions, and all analysis tools.

---

## Command Line Usage

### Screen Mode
Finds top trading opportunities:
```bash
python main.py --mode screen
```
- Screens by market cap, momentum, RSI
- Returns top 10 most promising tickers
- Saves results with scores and metrics

### Analyze Mode
Deep analysis of a specific ticker:
```bash
python main.py --mode analyze --ticker TSLA
```
Output includes:
- AI-generated trading signal (BUY/SELL/HOLD)
- Confidence score (0-100%)
- Sentiment analysis from multiple sources
- Technical indicators (RSI, MACD, Moving Averages)
- Price targets and stop-loss levels

### Options Mode
Analyze options for a ticker:
```bash
python main.py --mode options --ticker AAPL
```
- Shows options chain with liquidity
- Detects unusual options activity
- Suggests optimal options strategies

### Futures Mode
Analyze futures contracts:
```bash
python main.py --mode futures
python main.py --mode futures --ticker ES  # Specific contract
```
Analyzes:
- E-mini S&P 500 (ES)
- E-mini NASDAQ (NQ)
- Crude Oil (CL)
- Gold (GC)
- And more...

### Backtest Mode
Test strategies on historical data:
```bash
python main.py --mode backtest --ticker AAPL --strategy ma_crossover --days 252
```

Available strategies:
- `ma_crossover`: Moving Average Crossover
- `rsi`: RSI Mean Reversion
- `buy_hold`: Buy and Hold (benchmark)
- `compare`: Compare all strategies

### Watch Mode
Live monitoring of top opportunities:
```bash
python main.py --mode watch
```
Updates every 15 minutes with latest signals.

### Memory Mode
View prediction history and accuracy:
```bash
python main.py --mode memory
python main.py --mode memory --ticker AAPL  # Specific ticker
```

---

## Interactive Dashboard

Launch the Streamlit dashboard:
```bash
streamlit run dashboard.py
```

### Dashboard Pages:

#### 1. Overview
- Market indices (S&P 500, NASDAQ, DOW, Russell 2000)
- Sector performance heatmap
- Top 5 trading opportunities with one-click analysis

#### 2. Screener
- Adjustable filters (market cap, RSI, volume)
- Visual results with color-coded performance
- Export results to CSV

#### 3. Stock Analysis
- Real-time price charts (candlestick with volume)
- AI analysis with signal and confidence
- Technical indicators display
- **Expert Opinions** section with weighted consensus

#### 4. Options Analysis
- Live options chain (calls & puts)
- Unusual activity alerts
- Strategy suggestions based on market outlook

#### 5. Expert Opinions
- Expert leaderboard (sorted by accuracy)
- Verification of past predictions
- Tracked experts:
  - Warren Buffett mentions
  - Cathie Wood/ARK Invest
  - Ray Dalio/Bridgewater
  - Bill Ackman
  - Michael Burry

#### 6. Predictions History
- All past AI predictions
- Outcome tracking (correct/incorrect)
- Accuracy metrics

---

## Trading Strategies

### Built-in Strategies:

#### 1. Momentum Strategy
- Screens for stocks with:
  - RSI between 30-70 (not oversold/overbought)
  - Price above MA-50 and MA-200
  - Volume surge (>1.5x average)
  - Positive 1-month momentum

#### 2. Swing Trading
- Uses ATR for stop-loss placement
- Risk:Reward ratio of 2:1
- Entry on pullbacks to moving averages

#### 3. Mean Reversion (RSI)
- Buy when RSI < 30
- Sell when RSI > 70
- Works best in sideways markets

#### 4. Moving Average Crossover
- Buy when Fast MA (20) crosses above Slow MA (50)
- Sell on opposite crossover
- Trend-following strategy

---

## Expert Tracking System

The system tracks predictions from well-known experts and publications, weighing their opinions based on historical accuracy.

### How It Works:
1. **Scrapes news** for expert mentions (Buffett, Wood, etc.)
2. **Analyzes sentiment** of their statements
3. **Records predictions** for future verification
4. **Verifies outcomes** after 30 days
5. **Updates accuracy scores** automatically

### View Expert Leaderboard:
```bash
python main.py --mode memory
# Or in Dashboard: Expert Opinions page
```

### Expert Weighting:
- Accuracy > 70%: Weight = 1.0 (highest trust)
- Accuracy 50-70%: Weight = 0.7
- Accuracy < 50%: Weight = 0.3 (low trust)

### Tracked Experts & Publications:
| Expert/Publication | Type | Weight |
|-------------------|------|--------|
| Warren Buffett | Investor | 1.0 |
| Cathie Wood (ARK) | Investor | 0.8 |
| Ray Dalio | Investor | 0.9 |
| Motley Fool | Publication | 0.7 |
| Seeking Alpha | Publication | 0.6 |
| Barron's | Publication | 0.8 |
| Bloomberg | Publication | 0.9 |
| Wall Street Journal | Publication | 0.85 |
| Finnhub Analysts | Professional | 0.8 |

---

## Memory & Prediction Tracking

The system remembers ALL past predictions and their outcomes, reducing the need for recomputation.

### Benefits:
1. **No redundant analysis** - Checks memory before recomputing
2. **Continuous learning** - Accuracy improves over time
3. **Historical context** - See past signals for same ticker
4. **Performance tracking** - Know which setups work best

### Memory Files:
- `memory/prediction_memory.json` - All predictions
- `memory/prediction_outcomes.json` - Verified outcomes
- `memory/experts_tracking.json` - Expert accuracy
- `memory/market_context.json` - Market regime

### View Memory:
```bash
python main.py --mode memory
```

---

## Backtesting

Test any strategy against historical data before risking real money.

### Usage:
```bash
# Test one strategy
python main.py --mode backtest --ticker AAPL --strategy ma_crossover --days 252

# Compare all strategies
python main.py --mode backtest --ticker AAPL --strategy compare --days 504
```

### Metrics Provided:
- Total return (%)
- Max drawdown (%)
- Number of trades
- Win rate (%)
- Equity curve visualization

### Example Backtest Output:
```
Strategy: ma_crossover
Return: 15.3%
Final Value: $115,300
Total Trades: 8
Max Drawdown: -8.2%
```

---

## Options Trading

### Analyze Options Chain:
```bash
python main.py --mode options --ticker TSLA
```

### Features:
1. **Liquidity filtering** - Only shows options with volume > 100
2. **Unusual activity detection** - Flags volume spikes (3x average)
3. **Strategy suggestions**:
   - Long Call/Put
   - Bull/Bear Spreads
   - Iron Condor
   - Straddle

### Options Signal Integration:
- If stock signal is BUY → Suggest bullish options strategies
- If stock signal is SELL → Suggest bearish strategies
- If NEUTRAL → Suggest range-bound strategies

---

## Futures Trading

### Analyze Futures:
```bash
python main.py --mode futures
```

### Available Contracts:
| Symbol | Underlying | Proxy ETF |
|--------|-----------|------------|
| ES | E-mini S&P 500 | SPY |
| NQ | E-mini NASDAQ-100 | QQQ |
| CL | Crude Oil | USO |
| GC | Gold | GLD |
| SI | Silver | SLV |
| ZN | 10Y Treasury | IEF |
| 6E | Euro | FXE |
| ZC | Corn | CORN |

### Intermarket Analysis:
- Dollar vs Gold (inverse correlation)
- Bonds vs Stocks (risk-on/off)
- Crude Oil vs Energy Stocks

### Spread Trading:
- Gold/Silver ratio analysis
- Sector rotation detection

---

## Advanced Features

### 1. Offline Computation Offloading
The system uses FREE online sources that pre-compute data server-side:
- **Finnhub**: Pre-computed sentiment scores
- **Alpha Vantage**: Pre-computed technical indicators
- **Yahoo Finance**: Pre-calculated fundamentals

This dramatically reduces your local compute needs.

### 2. Smart Screening
- Only analyzes top 10 candidates (saves compute)
- Checks memory before recomputing
- Focuses on high-probability setups

### 3. Sentiment Aggregation
Sources combined:
- News API (news articles)
- Finnhub (social sentiment)
- Reddit (r/wallstreetbets, r/investing)
- Expert opinions (weighted by accuracy)

### 4. Risk Management
- Max 10% per position
- Stop-loss based on ATR (2x)
- Take-profit at 2:1 reward:risk
- Max 20% drawdown limit

---

## Free Data Sources Summary

| Data Type | Source | Limit |
|-----------|--------|-------|
| Stock Prices | Yahoo Finance | Unlimited |
| Company Info | Yahoo Finance | Unlimited |
| News Articles | News API | 100/day |
| Social Sentiment | Finnhub | 60/min |
| Reddit Posts | Reddit API | Unlimited |
| Technical Indicators | Alpha Vantage | 5/min |
| Analyst Ratings | Finnhub | 60/min |
| Options Data | Yahoo Finance | Unlimited |

---

## Troubleshooting

### Common Issues:

#### 1. "No module named 'yfinance'"
```bash
pip install yfinance
```

#### 2. "News API error" or no news data
- Check your `.env` file has valid `NEWS_API_KEY`
- News API free tier: 100 requests/day

#### 3. "Finnhub API error"
- Verify `FINNHUB_API_KEY` in `.env`
- Free tier: 60 calls/minute

#### 4. Dashboard not loading
```bash
pip install streamlit plotly
streamlit run dashboard.py
```

#### 5. Charts not showing
```bash
pip install matplotlib seaborn
```

#### 6. "TA-Lib not found" (Windows)
```bash
pip install ta-lib-windows
```

---

## Making Money: Best Practices

1. **Start with paper trading** - Test strategies without real money
2. **Focus on top 5-10 opportunities** - System identifies these for you
3. **Check expert consensus** - Dashboard shows weighted expert opinions
4. **Review backtest results** - Only trade strategies with positive historical returns
5. **Set stop-losses** - Always use the suggested stop-loss levels
6. **Diversify** - Don't put all capital in one trade
7. **Monitor predictions** - Check `memory mode` to see what's working
8. **Be patient** - Let the system build prediction history for better accuracy

---

## Disclaimer

**This software is for educational and research purposes only.**
- Past performance does not guarantee future results
- Always do your own research before investing
- Never invest money you cannot afford to lose
- Consider consulting a financial advisor
- The developers are not financial advisors

---

## Support

For issues or questions:
- Check `USAGE.md` (this file)
- Review the code in `SmartTrader/` folder
- Examine `output/` folder for generated analysis

**Happy Trading! 📈💰**
