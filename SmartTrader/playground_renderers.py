"""
Playground Renderers - UI rendering functions for the Strategy Playground
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta

from playground_helpers import format_inr
from playground_backtests import (
    backtest_buffett_value,
    backtest_bulls_ai_momentum,
    backtest_indian_momentum,
    backtest_nifty_options_writer,
    backtest_buy_and_hold,
)


def render_header():
    """Render playground header"""
    st.markdown('<h1 class="main-header">🎮 Strategy Playground</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Compare strategy performance and see what works best</p>', unsafe_allow_html=True)
    st.divider()


def render_sidebar():
    """Render sidebar controls"""
    st.sidebar.title("Playground Settings")

    # Ticker selection
    st.sidebar.subheader("Stock Selection")
    ticker = st.sidebar.text_input("Ticker Symbol", value="RELIANCE.NS").upper()

    # Date range
    st.sidebar.subheader("Date Range")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=365),
            max_value=datetime.now()
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            max_value=datetime.now()
        )

    # Strategy selection
    st.sidebar.subheader("Strategies to Compare")
    strategies_selected = st.sidebar.multiselect(
        "Select Strategies",
        [
            "Buffett Value",
            "Bulls AI Momentum",
            "Indian Momentum",
            "Nifty Options Writer",
            "Buy and Hold (Benchmark)"
        ],
        default=[
            "Buffett Value",
            "Bulls AI Momentum",
            "Indian Momentum",
            "Buy and Hold (Benchmark)"
        ]
    )

    # Initial capital
    st.sidebar.subheader("Capital")
    initial_capital = st.sidebar.number_input(
        "Initial Capital (₹)",
        min_value=10000,
        max_value=10000000,
        value=100000,
        step=10000
    )

    # Run backtest button
    run_backtest = st.sidebar.button("🚀 Run Backtest", type="primary")

    st.sidebar.divider()
    st.sidebar.caption(f"Last run: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    return {
        'ticker': ticker,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'strategies': strategies_selected,
        'initial_capital': initial_capital,
        'run': run_backtest
    }


def run_backtests(settings):
    """Run all selected backtests"""
    results = {}

    with st.spinner("Running backtests... This may take a moment."):
        progress_bar = st.progress(0)
        total_strategies = len(settings['strategies'])
        progress_step = 1.0 / total_strategies if total_strategies > 0 else 1.0

        for i, strategy in enumerate(settings['strategies']):
            if strategy == "Buffett Value":
                results['Buffett Value'] = backtest_buffett_value(
                    settings['ticker'],
                    settings['start_date'],
                    settings['end_date'],
                    settings['initial_capital']
                )
            elif strategy == "Bulls AI Momentum":
                results['Bulls AI Momentum'] = backtest_bulls_ai_momentum(
                    settings['ticker'],
                    settings['start_date'],
                    settings['end_date'],
                    settings['initial_capital']
                )
            elif strategy == "Indian Momentum":
                results['Indian Momentum'] = backtest_indian_momentum(
                    settings['ticker'],
                    settings['start_date'],
                    settings['end_date'],
                    settings['initial_capital']
                )
            elif strategy == "Nifty Options Writer":
                results['Nifty Options Writer'] = backtest_nifty_options_writer(
                    settings['ticker'],
                    settings['start_date'],
                    settings['end_date'],
                    settings['initial_capital']
                )
            elif strategy == "Buy and Hold (Benchmark)":
                results['Buy and Hold (Benchmark)'] = backtest_buy_and_hold(
                    settings['ticker'],
                    settings['start_date'],
                    settings['end_date'],
                    settings['initial_capital']
                )

            progress_bar.progress(min((i + 1) * progress_step, 1.0))

        progress_bar.empty()

    return results


def render_strategy_comparison_table(results):
    """Render strategy comparison table"""
    st.markdown('<h2 class="sub-header">📊 Strategy Comparison</h2>', unsafe_allow_html=True)

    if not results:
        st.warning("No results to display. Please run backtest first.")
        return

    # Create comparison dataframe
    comparison_data = []

    for strategy_name, result in results.items():
        if 'error' in result:
            continue

        comparison_data.append({
            'Strategy': strategy_name,
            'Final Value (₹)': format_inr(result['final_value']),
            'Total Return (%)': result['return_pct'],
            'Max Drawdown (%)': result['max_drawdown_pct'],
            'Number of Trades': result['total_trades'],
            'Win Rate (%)': result['win_rate'],
            'Sharpe Ratio': result['sharpe_ratio'],
            'Sortino Ratio': result['sortino_ratio'],
        })

    if not comparison_data:
        st.error("No valid results to display.")
        return

    df = pd.DataFrame(comparison_data)

    # Display with colored values
    def color_returns(val):
        if isinstance(val, (int, float)):
            if val > 0:
                return 'color: #4CAF50; font-weight: bold;'
            elif val < 0:
                return 'color: #F44336; font-weight: bold;'
        return ''

    # Apply styling
    styled_df = df.style.applymap(
        color_returns,
        subset=['Total Return (%)', 'Max Drawdown (%)', 'Sharpe Ratio', 'Sortino Ratio']
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )

    # Highlight best performer
    best_strategy = max(results.items(), key=lambda x: x[1].get('return_pct', -999) if 'error' not in x[1] else -999)
    if 'error' not in best_strategy[1]:
        st.success(f"🏆 **Best Performer:** {best_strategy[0]} with {best_strategy[1]['return_pct']}% return")


def render_interactive_chart(results, ticker):
    """Render interactive price chart with buy/sell signals"""
    st.markdown('<h2 class="sub-header">📈 Interactive Chart</h2>', unsafe_allow_html=True)

    if not results:
        st.warning("No results to display.")
        return

    # Get data from first valid result
    data = None
    for strategy_name, result in results.items():
        if 'error' not in result and 'data' in result:
            data = result['data']
            break

    if data is None or data.empty:
        st.error("No data available for charting.")
        return

    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=('Price Chart', 'Volume')
    )

    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name='Price',
            showlegend=True
        ),
        row=1, col=1
    )

    # Add buy/sell signals for each strategy
    colors = {
        'Buffett Value': '#1E88E5',
        'Bulls AI Momentum': '#43A047',
        'Indian Momentum': '#FB8C00',
        'Nifty Options Writer': '#8E24AA',
        'Buy and Hold (Benchmark)': '#757575'
    }

    for strategy_name, result in results.items():
        if 'error' in result:
            continue

        # Buy signals
        if 'buy_signals' in result and result['buy_signals']:
            buy_dates = [s['date'] for s in result['buy_signals']]
            buy_prices = [s['price'] for s in result['buy_signals']]

            fig.add_trace(
                go.Scatter(
                    x=buy_dates,
                    y=buy_prices,
                    mode='markers',
                    name=f'{strategy_name} (Buy)',
                    marker=dict(
                        symbol='triangle-up',
                        size=10,
                        color=colors.get(strategy_name, '#000000'),
                        line=dict(width=2)
                    ),
                    showlegend=True
                ),
                row=1, col=1
            )

        # Sell signals
        if 'sell_signals' in result and result['sell_signals']:
            sell_dates = [s['date'] for s in result['sell_signals']]
            sell_prices = [s['price'] for s in result['sell_signals']]

            fig.add_trace(
                go.Scatter(
                    x=sell_dates,
                    y=sell_prices,
                    mode='markers',
                    name=f'{strategy_name} (Sell)',
                    marker=dict(
                        symbol='triangle-down',
                        size=10,
                        color=colors.get(strategy_name, '#000000'),
                        line=dict(width=2)
                    ),
                    showlegend=True
                ),
                row=1, col=1
            )

    # Add volume bars
    fig.add_trace(
        go.Bar(
            x=data.index,
            y=data['Volume'],
            name='Volume',
            marker_color='rgba(0, 0, 255, 0.3)'
        ),
        row=2, col=1
    )

    fig.update_layout(
        height=700,
        xaxis_rangeslider_visible=False,
        title=f"{ticker} - Strategy Signals",
        hovermode='x unified'
    )

    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # Equity Curve Comparison
    st.markdown('<h3 class="sub-header">💰 Equity Curves</h3>', unsafe_allow_html=True)

    equity_fig = go.Figure()

    for strategy_name, result in results.items():
        if 'error' not in result and 'equity_curve' in result:
            equity_curve = result['equity_curve']
            dates = data.index[:len(equity_curve)]

            equity_fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=equity_curve,
                    mode='lines',
                    name=strategy_name,
                    line=dict(width=2)
                )
            )

    equity_fig.update_layout(
        title='Portfolio Value Over Time',
        xaxis_title='Date',
        yaxis_title='Portfolio Value (₹)',
        height=500,
        hovermode='x unified'
    )

    st.plotly_chart(equity_fig, use_container_width=True)


def render_trades_table(results):
    """Render full lifecycle prediction display with all trades"""
    st.markdown('<h2 class="sub-header">📋 Trade Details</h2>', unsafe_allow_html=True)

    if not results:
        st.warning("No results to display.")
        return

    # Strategy selector
    selected_strategy = st.selectbox(
        "Select Strategy to View Trades",
        options=[name for name, result in results.items() if 'error' not in result]
    )

    if selected_strategy and selected_strategy in results:
        result = results[selected_strategy]

        if 'trades' in result and result['trades']:
            trades = result['trades']

            # Create trades dataframe
            trade_data = []
            buy_info = None

            for trade in trades:
                if trade['type'] == 'BUY':
                    buy_info = trade
                elif trade['type'] == 'SELL' and buy_info:
                    trade_data.append({
                        'Buy Date': buy_info['date'],
                        'Buy Price (₹)': f"₹{buy_info['price']:.2f}",
                        'Sell Date': trade['date'],
                        'Sell Price (₹)': f"₹{trade['price']:.2f}",
                        'Profit/Loss (₹)': f"₹{trade.get('profit', 0):.2f}",
                        'Return (%)': f"{((trade['price'] - buy_info['price']) / buy_info['price'] * 100):.2f}%",
                        'Buy Reason': buy_info.get('reason', 'N/A'),
                        'Sell Reason': trade.get('reason', 'N/A')
                    })
                    buy_info = None

            if trade_data:
                df = pd.DataFrame(trade_data)

                # Style the dataframe
                def color_pnl(val):
                    if '₹' in str(val):
                        num = float(val.replace('₹', '').replace(',', ''))
                        if num > 0:
                            return 'color: #4CAF50; font-weight: bold;'
                        elif num < 0:
                            return 'color: #F44336; font-weight: bold;'
                    return ''

                styled_df = df.style.applymap(color_pnl, subset=['Profit/Loss (₹)', 'Return (%)'])

                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No completed trades to display.")
        else:
            st.info("No trade data available for this strategy.")


def render_performance_metrics(results):
    """Render algorithm performance metrics"""
    st.markdown('<h2 class="sub-header">📈 Performance Metrics</h2>', unsafe_allow_html=True)

    if not results:
        st.warning("No results to display.")
        return

    # Create metrics dataframe
    metrics_data = []

    for strategy_name, result in results.items():
        if 'error' in result:
            continue

        metrics_data.append({
            'Strategy': strategy_name,
            'Sharpe Ratio': result.get('sharpe_ratio', 0),
            'Sortino Ratio': result.get('sortino_ratio', 0),
            'Calmar Ratio': result.get('calmar_ratio', 0),
            'Profit Factor': result.get('profit_factor', 0),
            'Max Drawdown (%)': result.get('max_drawdown_pct', 0),
            'Win Rate (%)': result.get('win_rate', 0),
            'Total Trades': result.get('total_trades', 0)
        })

    if not metrics_data:
        st.error("No valid results to display.")
        return

    df = pd.DataFrame(metrics_data)

    # Display as table
    st.dataframe(
        df.style.background_gradient(
            subset=['Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio'],
            cmap='RdYlGn'
        ).background_gradient(
            subset=['Max Drawdown (%)'],
            cmap='RdYlGn_r'
        ).background_gradient(
            subset=['Win Rate (%)'],
            cmap='RdYlGn'
        ),
        use_container_width=True,
        hide_index=True
    )

    # Radar chart for visual comparison
    st.markdown('<h3 class="sub-header">🎯 Strategy Comparison Radar</h3>', unsafe_allow_html=True)

    if len(metrics_data) > 1:
        # Normalize metrics for radar chart
        categories = ['Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio', 'Profit Factor', 'Win Rate (%)']

        radar_fig = go.Figure()

        for row in metrics_data:
            strategy_name = row['Strategy']
            values = []

            for cat in categories:
                val = row[cat]
                # Normalize values (simplified normalization)
                if cat == 'Max Drawdown (%)':
                    values.append(max(0, 1 - abs(val) / 100))
                else:
                    values.append(min(max(val / 3, 0), 1))  # Assuming 3 is a good max for ratios

            values.append(values[0])  # Close the polygon

            radar_fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories + [categories[0]],
                fill='toself',
                name=strategy_name
            ))

        radar_fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Strategy Comparison (Normalized)",
            height=500
        )

        st.plotly_chart(radar_fig, use_container_width=True)


def render_what_if_analysis(results, settings):
    """Render What-If Analysis"""
    st.markdown('<h2 class="sub-header">🤔 What-If Analysis</h2>', unsafe_allow_html=True)

    if not results or len(results) < 2:
        st.warning("Need at least 2 strategies to compare for What-If analysis.")
        return

    col1, col2 = st.columns(2)

    with col1:
        strategy_x = st.selectbox(
            "Strategy X (What if I used...)",
            options=[name for name, result in results.items() if 'error' not in result],
            index=0
        )

    with col2:
        strategy_y = st.selectbox(
            "Instead of Strategy Y (...instead of)",
            options=[name for name, result in results.items() if 'error' not in result],
            index=min(1, len(results) - 1)
        )

    if strategy_x and strategy_y and strategy_x != strategy_y:
        result_x = results[strategy_x]
        result_y = results[strategy_y]

        if 'error' not in result_x and 'error' not in result_y:
            col1, col2, col3 = st.columns(3)

            with col1:
                diff_value = result_x['final_value'] - result_y['final_value']
                diff_pct = result_x['return_pct'] - result_y['return_pct']

                st.metric(
                    "Portfolio Value Difference",
                    format_inr(abs(diff_value)),
                    f"{diff_pct:+.2f}%",
                    delta_color="normal" if diff_value > 0 else "inverse"
                )

            with col2:
                st.metric(
                    f"{strategy_x} Final Value",
                    format_inr(result_x['final_value'])
                )

            with col3:
                st.metric(
                    f"{strategy_y} Final Value",
                    format_inr(result_y['final_value'])
                )

            # What-if scenario description
            if diff_value > 0:
                st.success(
                    f"✅ If you had used **{strategy_x}** instead of **{strategy_y}**, "
                    f"you would have made an additional **{format_inr(diff_value)}** "
                    f"(+{diff_pct:.2f}%)!"
                )
            elif diff_value < 0:
                st.error(
                    f"❌ If you had used **{strategy_x}** instead of **{strategy_y}**, "
                    f"you would have lost **{format_inr(abs(diff_value))}** "
                    f"({diff_pct:.2f}%)!"
                )
            else:
                st.info("Both strategies would have yielded the same result.")

            # Bar chart comparison
            comparison_df = pd.DataFrame([
                {'Strategy': strategy_x, 'Return (%)': result_x['return_pct']},
                {'Strategy': strategy_y, 'Return (%)': result_y['return_pct']}
            ])

            fig = px.bar(
                comparison_df,
                x='Strategy',
                y='Return (%)',
                color='Return (%)',
                color_continuous_scale=['red', 'yellow', 'green'],
                title="Return Comparison"
            )

            st.plotly_chart(fig, use_container_width=True)
