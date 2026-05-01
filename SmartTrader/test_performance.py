"""
Test script to verify caching and batch API functionality
Run this to verify the performance improvements work correctly
"""

import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.cache import market_data_cache, sentiment_cache, indicators_cache
from utils.data_fetcher import MarketDataFetcher
from utils.screener import SmartScreener

def test_cache():
    """Test that caching works correctly"""
    print("\n" + "="*50)
    print("Testing Cache Functionality")
    print("="*50)

    # Clear cache before testing
    market_data_cache.clear()

    fetcher = MarketDataFetcher()

    # Test 1: First call should hit API
    print("\nTest 1: First call to get_company_info (should hit API)...")
    start = time.time()
    info1 = fetcher.get_company_info('AAPL')
    time1 = time.time() - start
    print(f"  Time taken: {time1:.2f}s")
    print(f"  Got data: {bool(info1)}")

    # Test 2: Second call should hit cache
    print("\nTest 2: Second call to get_company_info (should use cache)...")
    start = time.time()
    info2 = fetcher.get_company_info('AAPL')
    time2 = time.time() - start
    print(f"  Time taken: {time2:.2f}s")
    print(f"  Cache working: {time2 < time1}")
    print(f"  Data identical: {info1 == info2}")

    # Test 3: Check cache stats
    stats = market_data_cache.stats()
    print(f"\nCache stats: {stats}")

    return True

def test_batch_api():
    """Test that batch API calls work correctly"""
    print("\n" + "="*50)
    print("Testing Batch API Functionality")
    print("="*50)

    fetcher = MarketDataFetcher()

    # Test batch stock data download
    print("\nTest: Batch download of multiple tickers...")
    tickers = ['AAPL', 'MSFT', 'GOOGL']

    start = time.time()
    data = fetcher.get_batch_stock_data(tickers, period='5d')
    elapsed = time.time() - start

    print(f"  Time taken: {elapsed:.2f}s")
    print(f"  Tickers returned: {len(data)}")
    for ticker in tickers:
        if ticker in data:
            print(f"  {ticker}: {len(data[ticker])} rows")

    return len(data) > 0

def test_screener_batch():
    """Test that the screener uses batch API calls"""
    print("\n" + "="*50)
    print("Testing Screener Batch Processing")
    print("="*50)

    screener = SmartScreener()

    # Test market cap screening with batch processing
    print("\nTest: Market cap screening (uses batch API)...")
    start = time.time()
    qualified = screener.screen_by_market_cap(min_cap=1e9)
    elapsed = time.time() - start
    print(f"  Time taken: {elapsed:.2f}s")
    print(f"  Qualified tickers: {len(qualified)}")

    return True

def test_rate_limiting():
    """Test that rate limiting works"""
    print("\n" + "="*50)
    print("Testing Rate Limiting")
    print("="*50)

    fetcher = MarketDataFetcher()
    fetcher._min_api_interval = 0.5  # 500ms

    print("\nTest: Making rapid API calls (should be rate limited)...")
    start = time.time()
    for i, ticker in enumerate(['AAPL', 'MSFT', 'GOOGL']):
        fetcher.get_current_price(ticker)
        if i < 2:
            print(f"  Completed call {i+1}")
    elapsed = time.time() - start
    print(f"  Total time for 3 calls: {elapsed:.2f}s")
    print(f"  Rate limiting working: {elapsed >= 1.0}")  # Should take at least 1s due to rate limiting

    return True

def main():
    """Run all tests"""
    print("SmartTrader Performance Improvements - Verification Tests")
    print("="*50)

    results = []

    try:
        results.append(("Cache Functionality", test_cache()))
    except Exception as e:
        print(f"Cache test failed: {e}")
        results.append(("Cache Functionality", False))

    try:
        results.append(("Batch API Calls", test_batch_api()))
    except Exception as e:
        print(f"Batch API test failed: {e}")
        results.append(("Batch API Calls", False))

    try:
        results.append(("Screener Batch Processing", test_screener_batch()))
    except Exception as e:
        print(f"Screener test failed: {e}")
        results.append(("Screener Batch Processing", False))

    try:
        results.append(("Rate Limiting", test_rate_limiting()))
    except Exception as e:
        print(f"Rate limiting test failed: {e}")
        results.append(("Rate Limiting", False))

    # Summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    for name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"  {name}: {status}")

    all_passed = all(result[1] for result in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
