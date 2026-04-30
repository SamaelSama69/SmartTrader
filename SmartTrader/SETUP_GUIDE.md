# SmartTrader Setup Guide (Windows)

Complete step-by-step guide to set up SmartTrader on Windows systems.

## Prerequisites

- Windows 10/11
- Python 3.10+ (3.12 recommended for best compatibility)
- Git (optional, for updates)

## Option 1: Setup with Virtual Environment (venv) - Recommended

### Step 1: Create Virtual Environment

Open Command Prompt or PowerShell in the SmartTrader directory:

```cmd
cd "C:\Users\Sham\Desktop\Projects\NLP SENTIMENT ANALYSIS\SmartTrader"
python -m venv venv
```

### Step 2: Activate Virtual Environment

```cmd
venv\Scripts\activate
```

You should see `(venv)` appear at the start of your command prompt.

### Step 3: Install Dependencies

```cmd
pip install --upgrade pip
pip install streamlit pandas yfinance plotly requests python-dotenv
```

For full functionality (ML models, technical analysis):

```cmd
pip install -r requirements.txt
```

**Note for Python 3.14 users**: Many ML packages don't have pre-built wheels yet. Use Python 3.12 for full functionality.

## Option 2: Setup with Conda

### Step 1: Create Conda Environment

```cmd
conda create -n smarttrader python=3.12 -y
conda activate smarttrader
```

### Step 2: Install Dependencies

```cmd
pip install streamlit pandas yfinance plotly requests python-dotenv
pip install -r requirements.txt
```

## API Keys Setup

SmartTrader uses several free APIs. Create a `.env` file in the project root:

```cmd
copy con .env
```

Add the following keys (get them from the links provided):

```env
# Reddit API (for sentiment analysis)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=SmartTrader/1.0

# Zerodha API (for Indian market trading)
ZERODHA_API_KEY=your_zerodha_api_key
ZERODHA_API_SECRET=your_zerodha_api_secret

# Optional: News API
NEWS_API_KEY=your_news_api_key
```

### How to Get API Keys

1. **Reddit API**:
   - Go to https://www.reddit.com/prefs/apps
   - Click "Create App" or "Create Another App"
   - Select "script" type
   - Note the client ID (under the app name) and client secret
   - ![Reddit API Setup Screenshot Placeholder]

2. **Zerodha API**:
   - Log in to https://kite.zerodha.com
   - Go to Profile → API Keys
   - Create a new API application
   - Note the API key and secret
   - ![Zerodha API Setup Screenshot Placeholder]

3. **News API (Optional)**:
   - Sign up at https://newsapi.org/register
   - Get your free API key
   - ![News API Setup Screenshot Placeholder]

## First Run Tutorial

### Step 1: Activate Environment

```cmd
venv\Scripts\activate
```

### Step 2: Run the Dashboard

```cmd
streamlit run dashboard.py
```

Or if streamlit is not in PATH:

```cmd
python -m streamlit run dashboard.py
```

### Step 3: Access the Dashboard

- The dashboard will open automatically in your default browser
- If not, go to: http://localhost:8501
- You should see the SmartTrader Dashboard header

### Step 4: Explore Features

1. **Market Data**: View real-time stock prices using yfinance
2. **Sentiment Analysis**: Check news and social media sentiment
3. **Trading Signals**: View buy/sell recommendations
4. **Indian Markets**: Special section for NSE/BSE stocks

![Dashboard Screenshot Placeholder]

## Troubleshooting Common Issues

### Issue 1: "streamlit: command not found"

**Solution**: Run streamlit via python module:
```cmd
python -m streamlit run dashboard.py
```

Or add the Scripts directory to PATH:
```cmd
set PATH=%PATH%;C:\Users\Sham\AppData\Roaming\Python\Python314\Scripts
```

### Issue 2: UnicodeEncodeError on Windows

**Solution**: Set console encoding to UTF-8:
```cmd
chcp 65001
python -m streamlit run dashboard.py
```

### Issue 3: TA-Lib Installation Fails

**For Windows users**: Use the pre-built wheel:
```cmd
pip install ta-lib-windows
```

Or skip TA-Lib if you don't need technical analysis features.

### Issue 4: Python 3.14 Compatibility Issues

**Solution**: Use Python 3.12 instead:
```cmd
conda create -n smarttrader python=3.12 -y
conda activate smarttrader
```

### Issue 5: Dashboard Shows "Module Not Found"

**Solution**: Install missing module:
```cmd
pip install <missing_module_name>
```

Check the error message for the specific module name.

### Issue 6: Zerodha API Connection Fails

**Solution**:
- Verify API keys in `.env` file
- Ensure you have an active Zerodha account
- Check internet connection
- Zerodha API requires annual subscription (₹2000/year)

## Verify Installation

Run the quick test script to verify core functionality:

```cmd
python test_quick.py
```

You should see "All core tests passed!" if everything is set up correctly.
