"""
Playground - Compare strategy performance
Shows profit/loss for different algorithms on same data
"""

import streamlit as st
import warnings
from pathlib import Path
import sys

warnings.filterwarnings('ignore')

# Add project to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Page config
st.set_page_config(
    page_title="SmartTrader Playground",
    page_icon="🎮",
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
    .strategy-card {
        background-color: #F5F5F5;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1E88E5;
    }
    .profit {color: #4CAF50; font-weight: bold;}
    .loss {color: #F44336; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# Import from split modules
from playground_renderers import (
    render_header,
    render_sidebar,
    run_backtests,
    render_strategy_comparison_table,
    render_interactive_chart,
    render_trades_table,
    render_performance_metrics,
    render_what_if_analysis,
)


def main():
    """Main playground function"""
    render_header()

    # Render sidebar and get settings
    settings = render_sidebar()

    # Run backtest if button clicked
    if settings['run']:
        st.session_state['results'] = run_backtests(settings)
        st.session_state['settings'] = settings

    # Display results if available
    if 'results' in st.session_state and st.session_state['results']:
        results = st.session_state['results']
        settings = st.session_state['settings']

        # Strategy Comparison Table
        render_strategy_comparison_table(results)

        st.divider()

        # Interactive Chart
        render_interactive_chart(results, settings['ticker'])

        st.divider()

        # Performance Metrics
        render_performance_metrics(results)

        st.divider()

        # Trade Details
        render_trades_table(results)

        st.divider()

        # What-If Analysis
        render_what_if_analysis(results, settings)

    elif settings['run']:
        st.error("No results generated. Please check your settings and try again.")


if __name__ == "__main__":
    main()
