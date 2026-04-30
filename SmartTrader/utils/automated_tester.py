"""
Automated Testing System
Tests all algorithms and recommends the best one based on backtesting results
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
import json

from strategies.algorithms import AlgorithmSelector
from utils.backtester import Backtester
from strategies.stocks import StockStrategy
from strategies.options import OptionsAnalyzer


class AutomatedTester:
    """
    Automatically tests algorithms and recommends the best one
    Based on backtesting performance in current market conditions
    """

    def __init__(self):
        self.selector = AlgorithmSelector()
        self.backtester = Backtester()
        self.results_file = MEMORY_DIR / "algorithm_test_results.json"
        self.results = self._load_results()

    def _load_results(self) -> Dict:
        """Load previous test results"""
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'tests': [], 'last_update': '', 'best_algorithms': {}}

    def save(self):
        """Save test results"""
        with open(self.results_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

    def test_algorithm_on_ticker(self, algorithm_name: str, ticker: str, days: int = 252) -> Dict:
        """
        Test a specific algorithm on a ticker using backtesting
        """
        # This is a simplified test - in reality would implement the algorithm's logic
        # in the backtester

        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        # Run backtest with appropriate strategy based on algorithm
        if 'momentum' in algorithm_name or 'bulls' in algorithm_name:
            result = self.backtester.moving_average_crossover(ticker, start_date)
        elif 'value' in algorithm_name or 'buffett' in algorithm_name:
            result = self.backtester.buy_and_hold(ticker, start_date)
        elif 'dalio' in algorithm_name or 'all_weather' in algorithm_name:
            result = self.backtester.moving_average_crossover(ticker, start_date, fast_window=50, slow_window=100)
        else:
            result = self.backtester.moving_average_crossover(ticker, start_date)

        # Add algorithm info
        result['algorithm'] = algorithm_name
        result['ticker'] = ticker
        result['test_date'] = datetime.now().isoformat()

        return result

    def test_all_algorithms(self, tickers: List[str] = None, days: int = 252) -> Dict:
        """
        Test all algorithms on multiple tickers
        Returns performance summary
        """
        if tickers is None:
            tickers = ['AAPL', 'MSFT', 'GOOGL', 'SPY', 'QQQ']

        print(f"\n[AUTO-TEST] Testing all algorithms on {len(tickers)} tickers...")
        print(f"Backtest period: {days} days\n")

        all_results = {}

        for ticker in tickers:
            print(f"Testing {ticker}...")
            ticker_results = {}

            # Test each algorithm
            for algo_name in self.selector.algorithms.keys():
                try:
                    result = self.test_algorithm_on_ticker(algo_name, ticker, days)
                    if 'error' not in result:
                        ticker_results[algo_name] = {
                            'return_pct': result.get('return_pct', 0),
                            'max_drawdown': result.get('max_drawdown_pct', 0),
                            'trades': result.get('total_trades', 0),
                        }
                except Exception as e:
                    print(f"  Error testing {algo_name}: {e}")

            all_results[ticker] = ticker_results

        # Aggregate results
        algorithm_stats = {}

        for algo_name in self.selector.algorithms.keys():
            returns = []
            drawdowns = []

            for ticker, ticker_data in all_results.items():
                if algo_name in ticker_data:
                    returns.append(ticker_data[algo_name]['return_pct'])
                    drawdowns.append(abs(ticker_data[algo_name]['max_drawdown']))

            if returns:
                algorithm_stats[algo_name] = {
                    'avg_return_pct': round(sum(returns) / len(returns), 2),
                    'best_return_pct': round(max(returns), 2),
                    'worst_return_pct': round(min(returns), 2),
                    'avg_drawdown_pct': round(sum(drawdowns) / len(drawdowns), 2) if drawdowns else 0,
                    'tests_count': len(returns),
                    'score': self._calculate_algorithm_score(returns, drawdowns)
                }

        # Find best algorithm
        best_algo = max(algorithm_stats.items(), key=lambda x: x[1]['score']) if algorithm_stats else None

        # Save results
        test_result = {
            'timestamp': datetime.now().isoformat(),
            'tickers': tickers,
            'days': days,
            'algorithm_stats': algorithm_stats,
            'best_algorithm': best_algo[0] if best_algo else None,
            'best_score': best_algo[1]['score'] if best_algo else 0
        }

        self.results['tests'].append(test_result)
        self.results['last_update'] = datetime.now().isoformat()
        if best_algo:
            self.results['best_algorithms'][datetime.now().strftime('%Y-%m-%d')] = best_algo[0]
        self.save()

        return test_result

    def _calculate_algorithm_score(self, returns: List[float], drawdowns: List[float]) -> float:
        """Calculate a score for an algorithm (higher is better)"""
        if not returns:
            return 0.0

        avg_return = sum(returns) / len(returns)
        avg_drawdown = sum(drawdowns) / len(drawdowns) if drawdowns else 0

        # Score = return - drawdown penalty
        score = avg_return - (avg_drawdown * 0.5)
        return round(score, 2)

    def get_best_algorithm(self, market_regime: str = None) -> Dict:
        """
        Get the best algorithm recommendation
        Based on recent backtesting results and current market regime
        """
        if market_regime is None:
            market_regime = self.selector.get_market_regime()

        # Check recent test results (last 7 days)
        recent_tests = [
            t for t in self.results.get('tests', [])
            if (datetime.now() - datetime.fromisoformat(t['timestamp'])).days < 7
        ]

        if recent_tests:
            # Use most recent test
            latest = recent_tests[-1]
            best = latest.get('best_algorithm')

            if best:
                return {
                    'algorithm': best,
                    'source': 'backtest_results',
                    'score': latest.get('best_score', 0),
                    'market_regime': market_regime,
                    'last_test': latest['timestamp']
                }

        # Fall back to regime-based recommendation
        recommendation = self.selector.recommend_algorithm(None, market_regime)

        return {
            'algorithm': recommendation.get('recommended_algorithm'),
            'source': 'regime_based',
            'market_regime': market_regime,
            'confidence': recommendation.get('confidence', 0)
        }

    def get_algorithm_leaderboard(self) -> List[Dict]:
        """Get leaderboard of algorithms by performance"""
        all_stats = {}

        for test in self.results.get('tests', []):
            for algo, stats in test.get('algorithm_stats', {}).items():
                if algo not in all_stats:
                    all_stats[algo] = {'tests': 0, 'avg_score': 0, 'scores': []}

                all_stats[algo]['tests'] += 1
                all_stats[algo]['scores'].append(stats['score'])

        # Calculate averages
        leaderboard = []
        for algo, data in all_stats.items():
            avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
            leaderboard.append({
                'algorithm': algo,
                'avg_score': round(avg_score, 2),
                'total_tests': data['tests'],
                'best_score': round(max(data['scores']), 2) if data['scores'] else 0
            })

        return sorted(leaderboard, key=lambda x: x['avg_score'], reverse=True)

    def auto_select_and_execute(self, ticker: str) -> Dict:
        """
        Automatically select the best algorithm and generate a signal
        This is the main entry point for automated trading recommendations
        """
        print(f"\n[AUTO] Auto-selecting algorithm for {ticker}...")

        # Step 1: Get market regime
        market_regime = self.selector.get_market_regime()
        print(f"  Market Regime: {market_regime}")

        # Step 2: Get algorithm recommendation
        recommendation = self.selector.recommend_algorithm(ticker, market_regime)
        algo_name = recommendation.get('recommended_algorithm', 'bulls_ai_momentum')

        print(f"  Recommended Algorithm: {algo_name}")

        # Step 3: Run the algorithm
        algo = self.selector.algorithms.get(algo_name)
        if algo:
            hist = yf.Ticker(ticker).history(period='6mo')
            result = algo.analyze(ticker, hist)

            # Step 4: Combine with sentiment
            stock_strategy = StockStrategy()
            base_analysis = stock_strategy.analyze_ticker(ticker, detailed=False)

            # Weighted combination
            algo_weight = 0.6
            sentiment_weight = 0.4

            algo_signal = 1 if result.get('signal') == 'BUY' else -1 if result.get('signal') == 'SELL' else 0
            sentiment_signal = 1 if base_analysis.get('signal') == 'BUY' else -1 if base_analysis.get('signal') == 'SELL' else 0

            combined_score = (algo_signal * algo_weight) + (sentiment_signal * sentiment_weight)

            if combined_score > 0.3:
                final_signal = 'BUY'
            elif combined_score < -0.3:
                final_signal = 'SELL'
            else:
                final_signal = 'HOLD'

            return {
                'ticker': ticker,
                'algorithm_used': algo_name,
                'algorithm_signal': result.get('signal'),
                'algorithm_confidence': result.get('confidence', 0),
                'sentiment_signal': base_analysis.get('signal'),
                'sentiment_confidence': base_analysis.get('confidence', 0),
                'final_signal': final_signal,
                'combined_score': round(combined_score, 3),
                'market_regime': market_regime,
                'reasoning': result.get('signals', []),
                'timestamp': datetime.now().isoformat()
            }

        return {'error': 'Algorithm not found'}
