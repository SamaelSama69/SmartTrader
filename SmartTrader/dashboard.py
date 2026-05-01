"""
Interactive Dashboard - Streamlit-based dashboard for SmartTrader
Shows all data, predictions, expert opinions in an attractive interface
"""

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# config import removed (not directly used)
from utils.data_fetcher import MarketDataFetcher, NewsFetcher
from utils.sentiment_analyzer import SentimentAnalyzer
from utils.screener import SmartScreener
from utils.memory_manager import PredictionMemory
from utils.lifecycle_manager import LifecyclePrediction
from strategies.stocks import StockStrategy
from strategies.options import OptionsAnalyzer
from utils.expert_tracker import ExpertTracker

# Authentication setup
try:
    import streamlit_authenticator as stauth
    AUTH_ENABLED = True
except ImportError:
    AUTH_ENABLED = False
    print("streamlit-authenticator not installed. Dashboard will run without authentication.")

# Page config
st.set_page_config(
    page_title="SmartTrader Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1E88E5; text-align: center;}
    .sub-header {font-size: 1.5rem; color: #43A047; margin-top: 1rem;}
    .metric-positive {color: #4CAF50; font-weight: bold;}
    .metric-negative {color: #F44336; font-weight: bold;}
    .metric-neutral {color: #FF9800; font-weight: bold;}
    .expert-card {background-color: #F5F5F5; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;}
</style>
""", unsafe_allow_html=True)


def render_header():
    """Render dashboard header"""
    st.markdown('<h1 class="main-header">📈 SmartTrader Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">AI-Powered Trading Analysis System</p>', unsafe_allow_html=True)
    st.divider()


def render_sidebar():
    """Render sidebar navigation"""
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Overview", "Screener", "Stock Analysis", "Options Analysis", "Expert Opinions", "Predictions History", "Active Predictions"]
    )

    st.sidebar.divider()

    # Quick settings
    st.sidebar.subheader("Settings")
    ticker = st.sidebar.text_input("Ticker", value="AAPL").upper()
    refresh = st.sidebar.button("🔄 Refresh Data")

    st.sidebar.divider()
    st.sidebar.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    return page, ticker, refresh


def render_overview():
    """Render overview page"""
    st.markdown('<h2 class="sub-header">Market Overview</h2>', unsafe_allow_html=True)

    # Market indices
    col1, col2, col3, col4 = st.columns(4)

    indices = {'SPY': 'S&P 500', 'QQQ': 'NASDAQ', 'DIA': 'DOW', 'IWM': 'Russell 2000'}

    for idx, (ticker, name) in enumerate(indices.items()):
        try:
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period='1d')
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                prev = hist['Open'].iloc[-1]
                change_pct = ((current - prev) / prev) * 100

                col = [col1, col2, col3, col4][idx]
                with col:
                    st.metric(
                        name,
                        f"${current:.2f}",
                        f"{change_pct:+.2f}%",
                        delta_color="normal" if change_pct >= 0 else "inverse"
                    )
        except:
            pass

    st.divider()

    # Sector performance
    st.subheader("Sector Performance")
    screener = SmartScreener()
    sector_perf = screener.get_sector_performance()

    if sector_perf:
        df = pd.DataFrame(list(sector_perf.items()), columns=['Sector', 'Performance'])
        fig = px.bar(df, x='Sector', y='Performance',
                     color='Performance',
                     color_continuous_scale=['red', 'yellow', 'green'],
                     title="1-Month Sector Performance (%)")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Top opportunities
    st.subheader("🎯 Top Trading Opportunities")
    if st.button("Find Opportunities", type="primary"):
        with st.spinner("Screening for opportunities..."):
            opportunities = screener.get_top_opportunities(max_results=5)

            if opportunities:
                for opp in opportunities:
                    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
                    col1.metric("Ticker", opp['ticker'])
                    col2.metric("Price", f"${opp['price']:.2f}")
                    col3.metric("1M Chg", f"{opp['price_change_1m']:+.2f}%")
                    col4.metric("RSI", f"{opp['rsi']:.1f}")
                    col5.metric("Score", opp['score'])
                    st.divider()


def render_screener():
    """Render stock screener page"""
    st.markdown('<h2 class="sub-header">Stock Screener</h2>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        min_market_cap = st.number_input("Min Market Cap ($B)", value=1.0) * 1e9
    with col2:
        min_rsi = st.slider("Min RSI", 0, 100, 30)
    with col3:
        max_rsi = st.slider("Max RSI", 0, 100, 70)

    if st.button("Run Screener", type="primary"):
        with st.spinner("Screening stocks..."):
            screener = SmartScreener()
            results = screener.screen_by_momentum(
                screener.screen_by_market_cap(min_market_cap),
                min_rsi=min_rsi,
                max_rsi=max_rsi
            )

            if results:
                df = pd.DataFrame(results)

                # Display as table
                st.dataframe(
                    df.style.background_gradient(subset=['price_change_1m'], cmap='RdYlGn'),
                    use_container_width=True,
                    hide_index=True
                )

                # Chart
                fig = px.bar(df, x='ticker', y='score', color='price_change_1m',
                             title="Screened Stocks - Opportunity Score",
                             color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No stocks found matching criteria.")


def render_stock_analysis(ticker: str):
    """Render stock analysis page"""
    st.markdown(f'<h2 class="sub-header">Analysis: {ticker}</h2>', unsafe_allow_html=True)

    if not ticker:
        st.warning("Please enter a ticker in the sidebar.")
        return

    # Fetch data
    with st.spinner(f"Analyzing {ticker}..."):
        try:
            # Stock info
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period='6mo')

            # Header metrics
            col1, col2, col3, col4 = st.columns(4)

            current_price = hist['Close'].iloc[-1] if not hist.empty else 0
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            change = ((current_price - prev_close) / prev_close) * 100

            col1.metric("Current Price", f"${current_price:.2f}", f"{change:+.2f}%")
            col2.metric("Market Cap", f"${info.get('marketCap', 0) / 1e9:.1f}B")
            col3.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
            col4.metric("52W Range", f"${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}")

            # Price chart
            st.subheader("Price Chart")
            if not hist.empty:
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                    vertical_spacing=0.03, row_heights=[0.7, 0.3])

                # Candlestick chart
                fig.add_trace(go.Candlestick(
                    x=hist.index,
                    open=hist['Open'],
                    high=hist['High'],
                    low=hist['Low'],
                    close=hist['Close'],
                    name='Price'
                ), row=1, col=1)

                # Volume
                fig.add_trace(go.Bar(x=hist.index, y=hist['Volume'], name='Volume'), row=2, col=1)

                fig.update_layout(height=600, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

            # AI Analysis
            st.subheader("🤖 AI Analysis")

            strategy = StockStrategy()
            analysis = strategy.analyze_ticker(ticker)

            if 'error' not in analysis:
                col1, col2, col3 = st.columns(3)

                signal = analysis['signal']
                signal_color = 'green' if signal == 'BUY' else 'red' if signal == 'SELL' else 'orange'

                with col1:
                    st.markdown(f"**Signal:** <span style='color: {signal_color}; font-size: 1.5rem;'>{signal}</span>",
                                unsafe_allow_html=True)
                with col2:
                    st.metric("Confidence", f"{analysis['confidence']:.1%}")
                with col3:
                    sentiment = analysis['factors'].get('sentiment', {}).get('aggregate_sentiment', 0)
                    st.metric("Sentiment", f"{sentiment:.2f}")

                # Technical indicators
                st.subheader("Technical Indicators")
                tech = analysis['factors'].get('technical', {})

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("RSI", f"{tech.get('rsi', 0):.1f}")
                col2.metric("MACD Signal", tech.get('macd_signal', 'N/A'))
                col3.metric("MA Signal", tech.get('ma_signal', 'N/A'))
                col4.metric("Volume", tech.get('volume_signal', 'N/A'))

            # Expert Opinions
            st.subheader("👔 Expert Opinions")
            expert_tracker = ExpertTracker()
            consensus = expert_tracker.get_weighted_expert_consensus(ticker)

            if 'score' in consensus:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Expert Consensus", consensus['consensus'])
                with col2:
                    st.metric("Weighted Score", f"{consensus['score']:.3f}")
                with col3:
                    st.metric("Confidence", f"{consensus['confidence']:.1%}")

                # Show sources
                if 'sources' in consensus:
                    with st.expander("View Expert Sources"):
                        st.json(consensus['sources'])

        except Exception as e:
            st.error(f"Error analyzing {ticker}: {e}")


def render_options_analysis(ticker: str):
    """Render options analysis page"""
    st.markdown('<h2 class="sub-header">Options Analysis</h2>', unsafe_allow_html=True)

    if not ticker:
        st.warning("Please enter a ticker.")
        return

    with st.spinner("Analyzing options..."):
        analyzer = OptionsAnalyzer()
        chain = analyzer.get_options_chain(ticker)

        if 'error' in chain:
            st.error(chain['error'])
            return

        st.info(f"Expiration: {chain['expiration']}")

        # Options flow
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📈 Calls")
            if chain['calls']:
                calls_df = pd.DataFrame(chain['calls'])
                st.dataframe(calls_df, use_container_width=True, hide_index=True)

        with col2:
            st.subheader("📉 Puts")
            if chain['puts']:
                puts_df = pd.DataFrame(chain['puts'])
                st.dataframe(puts_df, use_container_width=True, hide_index=True)

        # Unusual activity
        st.subheader("🚨 Unusual Activity")
        unusual = analyzer.detect_unusual_options_activity(ticker)

        if unusual.get('unusual_activity'):
            for act in unusual.get('activities', []):
                st.warning(f"{act['type']} @ ${act['strike']}: Volume {act['volume']} (Avg: {act['avg_volume']:.0f})")
        else:
            st.info("No unusual activity detected.")

        # Strategy suggestions
        st.subheader("💡 Strategy Suggestions")
        stock_analysis = StockStrategy().analyze_ticker(ticker, detailed=False)
        direction = 'BULLISH' if stock_analysis.get('signal') == 'BUY' else 'BEARISH' if stock_analysis.get('signal') == 'SELL' else 'NEUTRAL'

        strategies = analyzer.suggest_options_strategy(ticker, direction)

        if 'suggested_strategies' in strategies:
            for s in strategies['suggested_strategies']:
                with st.expander(f"{s['name']}"):
                    st.write(f"**Description:** {s['description']}")
                    st.write(f"**Risk:** {s['risk']}")
                    st.write(f"**Best if:** {s['best_if']}")


def render_expert_opinions():
    """Render expert opinions page"""
    st.markdown('<h2 class="sub-header">Expert Opinions & Accuracy</h2>', unsafe_allow_html=True)

    expert_tracker = ExpertTracker()

    # Verify past predictions
    if st.button("Verify Past Predictions", type="primary"):
        with st.spinner("Verifying predictions..."):
            expert_tracker.verify_expert_predictions()
            st.success("Verification complete!")

    # Leaderboard
    st.subheader("🏆 Expert Leaderboard")
    leaderboard = expert_tracker.get_expert_leaderboard()

    if leaderboard:
        df = pd.DataFrame(leaderboard)
        st.dataframe(
            df.style.background_gradient(subset=['accuracy'], cmap='RdYlGn'),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No expert tracking data yet. Predictions will be tracked over time.")

    # Expert details
    st.subheader("👔 Tracked Experts")
    for expert, data in expert_tracker.tracked_experts.items():
        with st.expander(f"{expert.replace('_', ' ').title()}"):
            st.write(f"**Type:** {data['type']}")
            st.write(f"**Weight:** {data['weight']}")
            st.write(f"**Current Accuracy:** {data['accuracy']:.1%}")


def render_predictions_history():
    """Render predictions history page"""
    st.markdown('<h2 class="sub-header">Predictions History</h2>', unsafe_allow_html=True)

    memory = PredictionMemory()
    predictions = memory.memory.get('predictions', [])

    if not predictions:
        st.info("No predictions recorded yet. Start analyzing stocks to build history.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(predictions)

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Predictions", len(predictions))

    accuracy_data = memory.get_prediction_accuracy()
    col2.metric("Overall Accuracy", f"{accuracy_data['accuracy']:.1%}")

    recent = [p for p in predictions if datetime.fromisoformat(p['timestamp']) > datetime.now() - timedelta(days=7)]
    col3.metric("Past Week", len(recent))

    col4.metric("With Outcomes", sum(1 for p in predictions if p.get('outcome_recorded')))

    # Predictions table
    st.subheader("Recent Predictions")

    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp', ascending=False).head(50)

        # Expand prediction details
        for _, row in df.iterrows():
            with st.expander(f"{row['ticker']} - {row['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                pred = row['prediction']
                st.write(f"**Signal:** {pred.get('signal', 'N/A')}")
                st.write(f"**Confidence:** {pred.get('confidence', 0):.1%}")
                st.write(f"**Outcome Recorded:** {'Yes' if row.get('outcome_recorded') else 'No'}")

                if 'factors' in pred:
                    st.json(pred['factors'])


def render_active_predictions():
    """Render active lifecycle predictions panel"""
    st.markdown('<h2 class="sub-header">📊 Active Predictions</h2>', unsafe_allow_html=True)

    lifecycle_manager = LifecyclePrediction()
    active_predictions = lifecycle_manager.get_active_predictions()

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Active Predictions", len(active_predictions))

    if active_predictions:
        # Calculate total P&L
        total_pnl = 0
        profitable_count = 0
        for pred in active_predictions:
            try:
                ticker_obj = yf.Ticker(pred['ticker'])
                hist = ticker_obj.history(period='1d')
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    entry = pred['entry']['price']
                    pnl = ((current - entry) / entry) * 100
                    total_pnl += pnl
                    if pnl > 0:
                        profitable_count += 1
            except:
                pass

        col2.metric("Profitable", f"{profitable_count}/{len(active_predictions)}")
        col3.metric("Avg P&L", f"{total_pnl / len(active_predictions):.2f}%" if active_predictions else "0%")

        # Total days in trades
        total_days = sum(
            (datetime.now() - datetime.fromisoformat(pred['created_at'])).days
            for pred in active_predictions
        )
        col4.metric("Total Days Held", total_days)
    else:
        col2.metric("Profitable", "0")
        col3.metric("Avg P&L", "0%")
        col4.metric("Total Days Held", 0)

    st.divider()

    if not active_predictions:
        st.info("No active predictions. Use SmartTrader to analyze stocks and generate BUY signals to create predictions.")
        return

    # Display each active prediction
    for pred in active_predictions:
        with st.container():
            # Header with ticker and status
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"### {pred['ticker']}")
                st.caption(f"ID: {pred['id']} | Entry: {pred['entry']['date']}")

            # Get current price and P&L
            try:
                ticker_obj = yf.Ticker(pred['ticker'])
                hist = ticker_obj.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    entry_price = pred['entry']['price']
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100
                    pnl_dollars = current_price - entry_price

                    with col2:
                        delta_color = "normal" if pnl_pct >= 0 else "inverse"
                        st.metric(
                            "Current Price",
                            f"${current_price:.2f}",
                            f"{pnl_pct:+.2f}%",
                            delta_color=delta_color
                        )

                    with col3:
                        pnl_color = "metric-positive" if pnl_pct >= 0 else "metric-negative"
                        st.markdown(f"**P&L:** <span class='{pnl_color}'>${pnl_dollars:+.2f} ({pnl_pct:+.2f}%)</span>",
                                   unsafe_allow_html=True)
                else:
                    with col2:
                        st.metric("Current Price", "N/A")
                    with col3:
                        st.markdown("**P&L:** N/A")
            except:
                with col2:
                    st.metric("Current Price", "Error")
                with col3:
                    st.markdown("**P&L:** Error")

            # Entry and Exit Plan
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Entry Plan**")
                st.markdown(f"- Entry Price: `${pred['entry']['price']:.2f}`")
                st.markdown(f"- Signal: `{pred['entry']['signal']}`")
                st.markdown(f"- Confidence: `{pred['entry']['confidence']:.1%}`")
                if pred['entry']['reason']:
                    st.caption(f"Reason: {pred['entry']['reason']}")

            with col2:
                st.markdown("**Exit Plan**")
                st.markdown(f"- Target: `${pred['exit_plan']['target_price']:.2f}` ({((pred['exit_plan']['target_price'] / pred['entry']['price'] - 1) * 100):+.1f}%)")
                st.markdown(f"- Stop Loss: `${pred['exit_plan']['stop_loss']:.2f}` ({((pred['exit_plan']['stop_loss'] / pred['entry']['price'] - 1) * 100):+.1f}%)")
                st.markdown(f"- Expected Exit: `{pred['exit_plan']['target_date']}`")

            # Progress bar for target
            try:
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    entry = pred['entry']['price']
                    target = pred['exit_plan']['target_price']
                    stop = pred['exit_plan']['stop_loss']

                    # Calculate progress towards target
                    total_range = target - stop
                    current_progress = current - stop
                    progress_pct = min(max(current_progress / total_range, 0), 1)

                    st.progress(progress_pct, text=f"Progress to target: {progress_pct:.1%}")
            except:
                pass

            # Check if should sell
            sell_check = lifecycle_manager.should_sell_now(pred['ticker'])
            if sell_check['sell']:
                st.warning(f"🔔 **Sell Signal:** {sell_check['reason']} (Confidence: {sell_check['confidence']:.1%})")

            # Close Trade button
            if st.button(f"Close Trade - {pred['ticker']}", key=f"close_{pred['id']}"):
                try:
                    ticker_obj = yf.Ticker(pred['ticker'])
                    hist = ticker_obj.history(period='1d')
                    if not hist.empty:
                        exit_price = hist['Close'].iloc[-1]
                        result = lifecycle_manager.close_prediction(
                            pred['id'],
                            exit_price,
                            "Manual close from dashboard"
                        )
                        st.success(f"Trade closed! P&L: {result['pnl_pct']:.2f}% (${result['pnl_dollars']:.2f})")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error closing trade: {e}")

            st.divider()


def main():
    """Main dashboard function"""

    # Authentication check
    if AUTH_ENABLED:
        names = ["User"]
        usernames = ["user"]
        passwords = ["password"]  # In production, use hashed passwords from secrets.toml

        authenticator = stauth.Authenticate(names, usernames, passwords, "smarttrader_dashboard", "abcdef", cookie_expiry_days=30)

        name, authentication_status, username = authenticator.login("Login", "main")

        if authentication_status == False:
            st.error("Username/password is incorrect")
            return
        elif authentication_status is None:
            st.warning("Please enter your username and password")
            return

        st.success(f"Welcome {name}!")
        authenticator.logout("Logout", "sidebar")

    render_header()
    page, ticker, refresh = render_sidebar()

    if page == "Overview":
        render_overview()
    elif page == "Screener":
        render_screener()
    elif page == "Stock Analysis":
        render_stock_analysis(ticker)
    elif page == "Options Analysis":
        render_options_analysis(ticker)
    elif page == "Expert Opinions":
        render_expert_opinions()
    elif page == "Predictions History":
        render_predictions_history()
    elif page == "Active Predictions":
        render_active_predictions()


if __name__ == "__main__":
    main()
