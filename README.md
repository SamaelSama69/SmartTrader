# 🤖 SmartTrader

**AI-Powered Trading Analysis System with Indian Market Support**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Market](https://img.shields.io/badge/Market-NSE%20%7C%20BSE-orange)](https://nseindia.com)
[![Broker](https://img.shields.io/badge/Broker-Zerodha-blue)](https://zerodha.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

SmartTrader is a quantitative trading system built specifically for the Indian equity market (NSE/BSE). It combines 7 battle-tested algorithms, real-time regime detection, Kelly-sized position management, and a Streamlit dashboard — with optional live order execution via Zerodha.

---

## ✨ Features

- **7 Algorithms** — momentum, Buffett value (NSE-calibrated), Dalio all-weather, BullsAI, sector rotation, opening-range breakout, and Nifty options writing
- **Market Regime Detection** — automatically classifies the market into `BULL_TREND`, `BULL_VOLATILE`, `BEAR_TREND`, `BEAR_VOLATILE`, `SIDEWAYS_LOW_VOL`, or `CRISIS` and routes to the best algorithm for current conditions
- **Kelly Position Sizing** — confidence-based sizing with a circuit breaker after 3 consecutive losses
- **Multi-Position Portfolio** — hold up to 6 concurrent positions with sector concentration limits (max 30% per sector)
- **Trailing Stops** — 5% ATR-based trailing stop on every open position
- **Options Pricing** — Black-Scholes short-strangle simulation for `NiftyOptionsWriter` (not fake short-selling)
- **Indian Indicators** — intraday-correct VWAP, SuperTrend, CPR, Pivot levels
- **Sentiment Fusion** — VADER + Finnhub + NewsAPI + Reddit signal blending
- **Streamlit Dashboard** — live and paper-trading visual interface
- **Paper & Live Trading** — run fully simulated or connect to Zerodha for live orders
- **SQLite Memory** — prediction memory with auto-verified outcomes

---

## 📂 Project Structure

```
SmartTrader/
├── main.py                        # CLI entry point
├── config.py                      # All thresholds, paths, API keys
├── indian_config.py               # NSE-specific defaults
├── indian_market_optimizer.py     # 20-year NSE quant playbook
├── broker_integration.py          # ZerodhaBroker + stub brokers
├── dashboard.py                   # Streamlit visual dashboard
│
├── strategies/
│   ├── algorithms.py              # 7 algorithms + AlgorithmSelector
│   ├── stocks.py                  # StockStrategy, MomentumBreakout,
│   │                              # SectorRotation, OpeningRangeBreakout
│   ├── options.py                 # Options chain analysis
│   └── futures.py                 # Futures spread analysis
│
└── utils/
    ├── backtester.py              # backtest_algorithm() with Kelly sizing
    ├── cache.py                   # DiskCache (stable md5 hash)
    ├── data_fetcher.py            # MarketDataFetcher, news, Reddit
    ├── database.py                # SQLite backend
    ├── indian_indicators.py       # VWAP, SuperTrend, Pivots, CPR
    ├── lifecycle_manager.py       # Trade lifecycle with real exit prices
    ├── market_regime.py           # IndianMarketRegime detector
    ├── memory_manager.py          # PredictionMemory, auto_verify_outcomes
    ├── notifier.py                # Console + Email + Telegram alerts
    ├── nse_data.py                # NSE ticker fetching and conversion
    ├── options_pricer.py          # Black-Scholes premium calculator
    ├── performance_tracker.py     # Strategy attribution, Sharpe weights
    ├── portfolio.py               # Multi-position PortfolioManager
    ├── risk_manager.py            # Kelly sizing, circuit breaker
    ├── screener.py                # Smart batch screener
    ├── sentiment_analyzer.py      # VADER + Finnhub + NewsAPI fusion
    └── visualizer.py             # Charts and plot rendering
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/SamaelSama69/SmartTrader.git
cd SmartTrader
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env and fill in your keys
```

Required keys in `.env`:

```
ZERODHA_API_KEY=
ZERODHA_API_SECRET=
FINNHUB_API_KEY=
NEWS_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
```

### 3. Run

```bash
# Screen for top NSE opportunities
python main.py --mode screen

# Deep analysis on a single stock
python main.py --mode analyze --ticker RELIANCE.NS

# Paper trading watch mode
python main.py --mode watch --paper

# Launch visual dashboard
streamlit run dashboard.py
```

---

## 📊 CLI Modes

| Command | Description |
|---------|-------------|
| `python main.py --mode screen` | Scan for top NSE opportunities |
| `python main.py --mode analyze --ticker RELIANCE.NS` | Deep single-stock analysis |
| `python main.py --mode backtest --strategy momentum` | Run a full backtest |
| `python main.py --mode watch --paper` | Paper trading watch mode |
| `python main.py --mode watch --live` | ⚠️ Live order execution |
| `python main.py --mode breakout` | 52-week high breakout scan |
| `python main.py --mode sectors` | Sector rotation ranking |
| `python main.py --mode orb` | Opening range breakout scan |
| `python main.py --mode perf` | Strategy performance leaderboard |
| `python main.py --mode memory` | View prediction memory and outcomes |
| `python main.py --mode index` | Index-level market overview |
| `python main.py --mode lifecycle` | Trade lifecycle manager |
| `python main.py --mode check-sell` | Check open positions for sell signals |
| `python main.py --mode kill-switch` | Emergency close all positions |
| `streamlit run dashboard.py` | Launch Streamlit visual dashboard |

---

## 🧠 Algorithms

| ID | Name | Best Regime | Description |
|----|------|-------------|-------------|
| `indian_momentum` | Indian Momentum | `BULL_TREND` | NSE-calibrated momentum with SuperTrend |
| `buffett_value` | Buffett Value (NSE) | `SIDEWAYS_LOW_VOL` | P/E < 20, D/E < 1.0, calibrated for Nifty 50 |
| `dalio_all_weather` | Dalio All-Weather | `BEAR_VOLATILE` | Multi-asset regime balancing with cached data |
| `bulls_ai_style` | BullsAI Style | `BULL_VOLATILE` | Wilder RSI + volume surge detection |
| `sector_rotation` | Sector Rotation | `BULL_TREND` | Relative strength across NSE sectors |
| `opening_range_breakout` | ORB | `BULL_TREND` | First 15-min range breakout strategy |
| `nifty_options_writer` | Nifty Options Writer | `SIDEWAYS_LOW_VOL` | Black-Scholes short-strangle premium collection |

The `AlgorithmSelector` detects the current regime and automatically routes to the best algorithm(s) for conditions.

---

## 📈 Return Targets & Position Math

The system is designed around a **₹10,00,000 → ₹13,00,000 (30% gain)** annual target.

```
Required edge per month: ~2.2% net of costs

With 6 concurrent positions, 52 trades/year:
  Win rate needed:  55%+
  Avg win:          8–12%  (momentum + trailing stops)
  Avg loss:         3–5%   (ATR-based stops)
  Expectancy/trade: (0.55 × 0.10) − (0.45 × 0.04) = 3.7%
  Annual estimate:  3.7% × 52 ÷ 6 concurrent ≈ 32%
```

This math requires: regime filtering, multi-position sizing, trailing stops, and Kelly sizing. A single-position flat-sized system delivers 8–12% at best.

---

## 🔒 Risk Controls

- **Kelly Position Sizing** — sizes each position by signal confidence, win rate, avg win/loss
- **Circuit Breaker** — halts new entries after 3 consecutive losses
- **Sector Concentration Limit** — max 30% of capital in any single sector
- **Trailing Stop** — 5% trailing stop updated every bar
- **Kill Switch** — `--mode kill-switch` closes all open positions immediately
- **Crisis Regime** — no new entries when `IndianMarketRegime` returns `CRISIS`

---

## 🏗️ Architecture

```
Market Data (yfinance / NSE API)
        │
        ▼
IndianMarketRegime ──► AlgorithmSelector
        │                      │
        │              selects best algo(s)
        │                      │
        ▼                      ▼
  Indian Indicators     Algorithm.analyze()
  (VWAP, SuperTrend,          │
   CPR, Pivots)               │ signal + confidence
                              ▼
                     RiskManager (Kelly sizing)
                              │
                              ▼
                     PortfolioManager
                     (sector limits, trailing stops)
                              │
                              ▼
                     ZerodhaBroker / PaperBroker
                              │
                              ▼
                     Notifier (Telegram / Email)
                     Dashboard (Streamlit)
```

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run a specific test
python -m pytest tests/test_algorithms.py::test_regime_routing -v
```

Pre-commit checklist:

```bash
# Syntax check all Python files
python3 -c "import ast,os; [ast.parse(open(os.path.join(r,f)).read()) \
  for r,d,fs in os.walk('.') for f in fs if f.endswith('.py')]"

# Check for accidental flat sizing
grep -n "0.20\|0\.20)" utils/backtester.py

# Confirm README is at repo root
ls README.md
```

---

## 📦 Requirements

- Python 3.10+
- `yfinance`, `pandas`, `numpy`, `scipy`
- `streamlit` (dashboard)
- `kiteconnect` (Zerodha live trading)
- `vaderSentiment`, `praw` (sentiment)
- `pytest` (testing)

Install all:

```bash
pip install -r requirements.txt
```

---

## ⚠️ Disclaimer

SmartTrader is an experimental research tool. It is **not financial advice**. Trading equities and derivatives carries significant risk of capital loss. The authors accept no liability for trading decisions made using this software. Always test thoroughly in paper mode before risking real capital. Use `--mode watch --live` at your own risk.

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Run the full test suite: `python -m pytest tests/ -v`
4. Commit with a semantic message: `git commit -m "feat: description"`
5. Open a pull request

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

*Built by [SamaelSama69](https://github.com/SamaelSama69) with ❤️ and Claude*
