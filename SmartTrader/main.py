"""
SmartTrader Main Orchestrator
Analyzes markets, stocks, options, and futures for profitable trading opportunities
Supports both US and Indian (NSE) markets
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import json

# Add project to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import *
from utils.data_fetcher import MarketDataFetcher, NewsFetcher, RedditSentimentFetcher
from utils.sentiment_analyzer import SentimentAnalyzer, TechnicalSentimentAnalyzer
from utils.screener import SmartScreener
from utils.memory_manager import PredictionMemory, MarketContextMemory
from utils.backtester import Backtester
from utils.visualizer import Visualizer
from strategies.stocks import StockStrategy
from strategies.options import OptionsAnalyzer
from strategies.futures import FuturesAnalyzer
from utils.lifecycle_manager import LifecyclePrediction

# Indian market support
from utils.nse_data import NSEDataFetcher, convert_to_nse_format, convert_from_nse_format
from utils.indian_indicators import is_expiry_day, is_budget_day
import indian_config as indian_cfg


class SmartTrader:
    """Main trading system orchestrator - Supports US and Indian markets"""

    def __init__(self, market: str = 'US'):
        """
        Initialize SmartTrader
        market: 'US' for US markets, 'IN' for Indian markets (NSE/BSE)
        """
        self.market = market.upper()

        # Initialize common components
        self.data_fetcher = MarketDataFetcher()
        self.news_fetcher = NewsFetcher()
        self.reddit_fetcher = RedditSentimentFetcher()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.tech_sentiment = TechnicalSentimentAnalyzer()
        self.screener = SmartScreener()
        self.memory = PredictionMemory()
        self.market_context = MarketContextMemory()
        self.backtester = Backtester()
        self.visualizer = Visualizer()
        self.stock_strategy = StockStrategy()
        self.options_analyzer = OptionsAnalyzer()
        self.futures_analyzer = FuturesAnalyzer()

        # Indian market components (lazy loaded)
        self.nse_fetcher = None
        if self.market == 'IN':
            self.nse_fetcher = NSEDataFetcher()

        # Lifecycle prediction manager
        self.lifecycle_manager = LifecyclePrediction()

        # Print banner
        print("=" * 60)
        if self.market == 'IN':
            print("  SmartTrader - Indian Market Analysis System (NSE/BSE)")
            print("=" * 60)
            print(f"  Market: NSE/BSE")
            print(f"  Trading Hours: 9:15 AM - 3:30 PM IST")
            print(f"  Expiry Day: Thursday")
            if is_expiry_day():
                print(f"  *** TODAY IS EXPIRY DAY (Thursday) ***")
            if is_budget_day():
                print(f"  *** TODAY IS BUDGET DAY (Feb 1st) - High Volatility Expected ***")
        else:
            print("  SmartTrader - AI Trading Analysis System (US Markets)")
            print("=" * 60)
        print()

    def normalize_ticker(self, ticker: str) -> str:
        """Normalize ticker based on market"""
        if self.market == 'IN':
            return convert_to_nse_format(ticker)
        return ticker.upper()

    def screen_opportunities(self):
        """Screen for top trading opportunities"""
        print("\n[SCREEN] Finding top trading opportunities...")

        if self.market == 'IN' and self.nse_fetcher:
            return self.screen_indian_opportunities()

        results = self.screener.get_top_opportunities()

        if results:
            print(f"\nTop {len(results)} opportunities found:")
            print("-" * 80)
            print(f"{'Ticker':<8} {'Score':<6} {'Price':<10} {'1M Chg%':<10} {'RSI':<8} {'Volume':<8}")
            print("-" * 80)

            for r in results:
                print(f"{r['ticker']:<8} {r['score']:<6} ${r['price']:<9} {r['price_change_1m']:>6}%   {r['rsi']:<8} {r['volume_surge']:<8.1f}x")

            # Save results
            output_file = OUTPUT_DIR / "screened_opportunities.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {output_file}")

            # Create visualization
            self.visualizer.plot_screener_results(results)
        else:
            print("No opportunities found.")

        return results

    def screen_indian_opportunities(self):
        """Screen for Indian market opportunities"""
        print("\n[SCREEN] Finding top Indian market opportunities...")

        # Get popular Indian stocks
        indian_stocks = self.nse_fetcher.get_nifty_50_tickers()

        results = []
        for ticker in indian_stocks[:20]:  # Limit for performance
            try:
                analysis = self.analyze_ticker(ticker, detailed=False)
                if 'error' not in analysis and analysis.get('signal') in ['BUY', 'SELL']:
                    results.append({
                        'ticker': ticker,
                        'signal': analysis['signal'],
                        'confidence': analysis['confidence'],
                        'price': analysis.get('current_price', 0)
                    })
            except:
                continue

        if results:
            results.sort(key=lambda x: x['confidence'], reverse=True)
            print(f"\nTop {len(results)} Indian opportunities found:")
            for r in results[:10]:
                print(f"  {r['ticker']:<15} {r['signal']:<6} (Conf: {r['confidence']:.1%}) @ {r['price']:.2f}")
        else:
            print("No opportunities found.")

        return results

    def analyze_ticker(self, ticker: str, detailed: bool = True):
        """Full analysis of a single ticker"""
        # Normalize ticker
        ticker = self.normalize_ticker(ticker)

        print(f"\n[ANALYZE] Analyzing {ticker}...")

        # Check memory first
        if not self.memory.should_recompute(ticker):
            print("  Using cached analysis (use --force to override)")
            past = self.memory.get_past_predictions(ticker, days=1)
            if past:
                return past[-1]['prediction']

        # Run analysis
        analysis = self.stock_strategy.analyze_ticker(ticker, detailed)

        if 'error' in analysis:
            print(f"  Error: {analysis['error']}")
            return analysis

        # Print results
        print(f"\n{'=' * 60}")
        print(f"  Analysis for {ticker}")
        print(f"{'=' * 60}")
        print(f"  Signal: {analysis['signal']} (Confidence: {analysis['confidence']:.1%})")
        print(f"  Current Price: ${analysis.get('current_price', 'N/A')}")

        if analysis.get('price_target'):
            print(f"  Price Target: ${analysis['price_target']}")
            print(f"  Stop Loss: ${analysis['stop_loss']}")

        print(f"\n  Sentiment: {analysis['factors'].get('sentiment', {}).get('aggregate_sentiment', 0):.2f}")
        print(f"  RSI: {analysis['factors'].get('technical', {}).get('rsi', 'N/A')}")
        print(f"  MACD Signal: {analysis['factors'].get('technical', {}).get('macd_signal', 'N/A')}")
        print(f"  MA Signal: {analysis['factors'].get('technical', {}).get('ma_signal', 'N/A')}")

        # Save analysis
        output_file = OUTPUT_DIR / f"{ticker}_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        print(f"\n  Analysis saved to: {output_file}")

        # Create lifecycle prediction if BUY signal
        if analysis.get('signal') == 'BUY' and 'current_price' in analysis:
            print(f"\n  [LIFECYCLE] Creating full trade prediction...")
            try:
                lifecycle_pred = self.lifecycle_manager.create_prediction(
                    ticker, 'BUY', analysis['current_price'], analysis
                )
                print(f"    Prediction ID: {lifecycle_pred['id']}")
                print(f"    Entry: ${lifecycle_pred['entry']['price']:.2f}")
                print(f"    Target: ${lifecycle_pred['exit_plan']['target_price']:.2f}")
                print(f"    Stop Loss: ${lifecycle_pred['exit_plan']['stop_loss']:.2f}")
                print(f"    Expected Exit: {lifecycle_pred['exit_plan']['target_date']}")
            except Exception as e:
                print(f"    Warning: Could not create lifecycle prediction: {e}")

        # Create visualization
        self.visualizer.create_summary_dashboard(analysis)
        self.visualizer.plot_price_with_signals(ticker)

        return analysis

    def analyze_options(self, ticker: str):
        """Analyze options for a ticker"""
        ticker = self.normalize_ticker(ticker)
        print(f"\n[OPTIONS] Analyzing options for {ticker}...")

        # Get stock signal first
        stock_analysis = self.analyze_ticker(ticker, detailed=False)
        direction = 'BULLISH' if stock_analysis.get('signal') == 'BUY' else 'BEARISH' if stock_analysis.get('signal') == 'SELL' else 'NEUTRAL'

        # Get options chain
        chain = self.options_analyzer.get_options_chain(ticker)
        if 'error' in chain:
            print(f"  Error: {chain['error']}")
            return chain

        print(f"\n  Options Expiration: {chain['expiration']}")
        print(f"  Calls Available: {len(chain['calls'])}")
        print(f"  Puts Available: {len(chain['puts'])}")

        # Check unusual activity
        unusual = self.options_analyzer.detect_unusual_options_activity(ticker)
        if unusual.get('unusual_activity'):
            print(f"\n  UNUSUAL OPTIONS ACTIVITY DETECTED!")
            print(f"  Activity Count: {unusual['activity_count']}")
            for act in unusual['activities'][:5]:
                print(f"    - {act['type']} @ ${act['strike']}: Volume {act['volume']} (Avg: {act['avg_volume']:.0f})")

        # Suggest strategies
        strategies = self.options_analyzer.suggest_options_strategy(ticker, direction)
        if 'error' not in strategies:
            print(f"\n  Suggested Strategies for {direction} outlook:")
            for s in strategies['suggested_strategies']:
                print(f"    - {s['name']}: {s['description']}")
                print(f"      Risk: {s['risk']} | Best if: {s['best_if']}")

        return {'chain': chain, 'unusual': unusual, 'strategies': strategies}

    def analyze_futures(self, symbol: str = None):
        """Analyze futures contracts"""
        print(f"\n[FUTURES] Analyzing futures...")

        symbols = [symbol] if symbol else ['ES', 'NQ', 'CL', 'GC']

        results = {}
        for sym in symbols:
            print(f"\n  Analyzing {sym}...")
            result = self.futures_analyzer.generate_futures_signal(sym)
            results[sym] = result

            if 'error' not in result:
                print(f"    Signal: {result['signal']} (Confidence: {result['confidence']:.1%})")
                analysis = result.get('analysis', {})
                print(f"    Trend: {analysis.get('trend', 'N/A')}")
                print(f"    Price: ${analysis.get('current_price', 'N/A')}")

        # Intermarket analysis
        print(f"\n  Intermarket Relationships:")
        intermarket = self.futures_analyzer.analyze_intermarket_relationships()
        for key, value in intermarket.items():
            print(f"    {key}: {value}")

        # Spread opportunities
        spreads = self.futures_analyzer.get_futures_spread_opportunity()
        if spreads:
            print(f"\n  Spread Opportunities:")
            for s in spreads:
                print(f"    - {s['spread']}: {s['signal']} ({s['reason']})")

        return results

    def analyze_indian_index(self, index: str = 'NIFTY50'):
        """Analyze Indian indices like Nifty, BankNifty"""
        print(f"\n[INDEX] Analyzing {index}...")

        index_map = {
            'NIFTY50': '^NSEI',
            'BANKNIFTY': '^NSEBANK',
        }

        symbol = index_map.get(index.upper())
        if not symbol:
            print(f"Unknown index: {index}")
            return None

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='6mo')

            if hist.empty:
                print("No data available")
                return None

            current_price = hist['Close'].iloc[-1]

            # Calculate basic indicators
            ma_50 = hist['Close'].rolling(50).mean().iloc[-1]
            ma_200 = hist['Close'].rolling(200).mean().iloc[-1] if len(hist) >= 200 else ma_50

            print(f"\n  {index} Analysis:")
            print(f"  Current Price: {current_price:.2f}")
            print(f"  50-day MA: {ma_50:.2f}")
            print(f"  200-day MA: {ma_200:.2f}")

            if current_price > ma_50 > ma_200:
                signal = 'BULLISH'
                print(f"  Signal: BULLISH (Strong Uptrend)")
            elif current_price < ma_50 < ma_200:
                signal = 'BEARISH'
                print(f"  Signal: BEARISH (Strong Downtrend)")
            else:
                signal = 'NEUTRAL'
                print(f"  Signal: NEUTRAL (Consolidation)")

            return {
                'index': index,
                'price': current_price,
                'ma_50': ma_50,
                'ma_200': ma_200,
                'signal': signal
            }

        except Exception as e:
            print(f"Error: {e}")
            return None

    def run_backtest(self, ticker: str, strategy: str = 'ma_crossover', days: int = 252):
        """Run backtest on a strategy"""
        ticker = self.normalize_ticker(ticker)
        print(f"\n[BACKTEST] Running backtest for {ticker}...")

        start_date = (datetime.now() - __import__('pandas').Timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        if strategy == 'ma_crossover':
            result = self.backtester.moving_average_crossover(ticker, start_date, end_date)
        elif strategy == 'rsi':
            result = self.backtester.rsi_strategy(ticker, start_date, end_date)
        elif strategy == 'buy_hold':
            result = self.backtester.buy_and_hold(ticker, start_date, end_date)
        elif strategy == 'compare':
            result = self.backtester.compare_strategies(ticker, start_date, end_date)
        else:
            print(f"Unknown strategy: {strategy}")
            return None

        if 'error' in result:
            print(f"  Error: {result['error']}")
            return result

        print(f"\n  Strategy: {result.get('strategy', 'N/A')}")
        print(f"  Return: {result.get('return_pct', 0):.2f}%")
        print(f"  Final Value: ${result.get('final_value', 0):.2f}")
        print(f"  Total Trades: {result.get('total_trades', 0)}")

        if 'max_drawdown_pct' in result:
            print(f"  Max Drawdown: {result['max_drawdown_pct']:.2f}%")

        # Save results
        output_file = OUTPUT_DIR / f"{ticker}_{strategy}_backtest.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n  Results saved to: {output_file}")

        # Visualize
        self.visualizer.plot_backtest_results({'strategies': {strategy: result}})

        return result

    def watch_mode(self, refresh_minutes: int = 15):
        """Live monitoring mode"""
        print(f"\n[WATCH] Starting live watch mode (refresh: {refresh_minutes} min)...")
        print("Press Ctrl+C to stop\n")

        import time
        try:
            while True:
                # Get top opportunities
                opportunities = self.screener.get_top_opportunities(max_results=5)

                print(f"\n{'=' * 60}")
                print(f"  Watch Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"{'=' * 60}")

                for opp in opportunities:
                    analysis = self.analyze_ticker(opp['ticker'], detailed=False)
                    if 'error' not in analysis:
                        print(f"  {opp['ticker']}: {analysis['signal']} @ ${analysis.get('current_price', 0):.2f} (Conf: {analysis['confidence']:.1%})")

                print(f"\n  Next update in {refresh_minutes} minutes...")
                time.sleep(refresh_minutes * 60)

        except KeyboardInterrupt:
            print("\n\nWatch mode stopped.")

    def show_memory(self, ticker: str = None):
        """Show prediction memory"""
        print(f"\n[MEMORY] Prediction Memory")

        if ticker:
            ticker = self.normalize_ticker(ticker)
            stats = self.memory.get_ticker_stats(ticker)
            print(f"\n  Stats for {ticker}:")
            print(f"    Total Predictions: {stats['total_predictions']}")
            print(f"    Accuracy: {stats['prediction_accuracy']:.1%}")
            print(f"    Signal Distribution: {stats['signal_distribution']}")
        else:
            accuracy = self.memory.get_prediction_accuracy()
            print(f"\n  Overall Accuracy: {accuracy.get('accuracy', 0):.1%}")
            print(f"  Total Predictions: {accuracy.get('total', 0)}")
            print(f"  Correct: {accuracy.get('correct', 0)}")

    def show_lifecycle(self, ticker: str = None):
        """Show active lifecycle predictions"""
        print(f"\n[LIFECYCLE] Active Predictions")

        if ticker:
            ticker = self.normalize_ticker(ticker)
            active = self.lifecycle_manager.get_active_for_ticker(ticker)
            print(f"\n  Active predictions for {ticker}:")
        else:
            active = self.lifecycle_manager.get_active_predictions()
            print(f"\n  All active predictions ({len(active)} total):")

        if not active:
            print("  No active predictions found.")
            return

        for pred in active:
            print(f"\n{'=' * 50}")
            print(f"  ID: {pred['id']} | Ticker: {pred['ticker']}")
            print(f"  Entry: ${pred['entry']['price']:.2f} on {pred['entry']['date']}")
            print(f"  Target: ${pred['exit_plan']['target_price']:.2f} | Stop: ${pred['exit_plan']['stop_loss']:.2f}")

            # Get current price and P&L
            try:
                ticker_obj = yf.Ticker(pred['ticker'])
                hist = ticker_obj.history(period='1d')
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    pnl_pct = ((current - pred['entry']['price']) / pred['entry']['price']) * 100
                    pnl_color = '+' if pnl_pct >= 0 else ''
                    print(f"  Current: ${current:.2f} | P&L: {pnl_color}{pnl_pct:.2f}%")
            except:
                print(f"  Current: Unable to fetch price")

    def check_sell(self, ticker: str):
        """Check if we should sell based on active predictions"""
        ticker = self.normalize_ticker(ticker)
        print(f"\n[CHECK SELL] Checking {ticker}...")

        result = self.lifecycle_manager.should_sell_now(ticker)

        print(f"\n  Ticker: {ticker}")
        print(f"  Should Sell: {result['sell']}")
        print(f"  Reason: {result['reason']}")
        print(f"  Confidence: {result['confidence']:.1%}")

        if 'pnl_pct' in result:
            pnl = result['pnl_pct']
            pnl_color = '+' if pnl >= 0 else ''
            print(f"  P&L: {pnl_color}{pnl:.2f}%")

        return result


def main():
    parser = argparse.ArgumentParser(description='SmartTrader - AI Trading Analysis System')

    parser.add_argument('--market', type=str, default='US', choices=['US', 'IN'],
                        help='Market: US (default) or IN (Indian/NSE)')

    parser.add_argument('--mode', type=str, default='screen',
                        choices=['screen', 'analyze', 'options', 'futures', 'backtest', 'watch', 'memory', 'index', 'lifecycle', 'check-sell'],
                        help='Operation mode')

    parser.add_argument('--ticker', type=str, help='Ticker symbol to analyze')
    parser.add_argument('--strategy', type=str, default='ma_crossover',
                        choices=['ma_crossover', 'rsi', 'buy_hold', 'compare'],
                        help='Backtest strategy')
    parser.add_argument('--days', type=int, default=252, help='Backtest period in days')
    parser.add_argument('--force', action='store_true', help='Force recomputation')
    parser.add_argument('--index', type=str, default='NIFTY50',
                        help='Index to analyze (for --mode index)')

    args = parser.parse_args()

    # Initialize system
    trader = SmartTrader(market=args.market)

    # Execute mode
    if args.mode == 'screen':
        trader.screen_opportunities()

    elif args.mode == 'analyze':
        if not args.ticker:
            print("Error: --ticker required for analyze mode")
            return
        trader.analyze_ticker(args.ticker)

    elif args.mode == 'options':
        if not args.ticker:
            print("Error: --ticker required for options mode")
            return
        trader.analyze_options(args.ticker)

    elif args.mode == 'futures':
        trader.analyze_futures(args.ticker)

    elif args.mode == 'backtest':
        if not args.ticker:
            print("Error: --ticker required for backtest mode")
            return
        trader.run_backtest(args.ticker, args.strategy, args.days)

    elif args.mode == 'watch':
        trader.watch_mode()

    elif args.mode == 'memory':
        trader.show_memory(args.ticker)

    elif args.mode == 'index':
        if args.market == 'IN':
            trader.analyze_indian_index(args.index)
        else:
            print("Index analysis only available for Indian market (use --market IN)")

    elif args.mode == 'lifecycle':
        trader.show_lifecycle(args.ticker)

    elif args.mode == 'check-sell':
        if not args.ticker:
            print("Error: --ticker required for check-sell mode")
            return
        trader.check_sell(args.ticker)


if __name__ == "__main__":
    import pandas as pd  # Needed for backtest
    main()
