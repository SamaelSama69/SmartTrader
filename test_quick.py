#!/usr/bin/env python
"""
Quick test script for SmartTrader core functionality.
Run this to verify your setup is working correctly.
"""

import sys
import traceback

def test_imports():
    """Test core package imports"""
    print("Testing core imports...")
    results = {}

    # Test streamlit
    try:
        import streamlit
        results["streamlit"] = f"OK (v{streamlit.__version__})"
    except ImportError as e:
        results["streamlit"] = f"FAIL: {e}"

    # Test pandas
    try:
        import pandas as pd
        results["pandas"] = f"OK (v{pd.__version__})"
    except ImportError as e:
        results["pandas"] = f"FAIL: {e}"

    # Test yfinance
    try:
        import yfinance as yf
        results["yfinance"] = f"OK (v{yf.__version__})"
    except ImportError as e:
        results["yfinance"] = f"FAIL: {e}"

    # Test plotly
    try:
        import plotly
        results["plotly"] = f"OK (v{plotly.__version__})"
    except ImportError as e:
        results["plotly"] = f"FAIL: {e}"

    # Test numpy
    try:
        import numpy as np
        results["numpy"] = f"OK (v{np.__version__})"
    except ImportError as e:
        results["numpy"] = f"FAIL: {e}"

    # Test requests
    try:
        import requests
        results["requests"] = f"OK (v{requests.__version__})"
    except ImportError as e:
        results["requests"] = f"FAIL: {e}"

    # Test python-dotenv
    try:
        import dotenv
        results["python-dotenv"] = "OK"
    except ImportError as e:
        results["python-dotenv"] = f"FAIL: {e}"

    return results

def test_config():
    """Test config loading"""
    print("\nTesting config loading...")
    try:
        # Import config at module level would be better, but using exec for simplicity
        import config
        print("[PASS] Config loaded successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Config loading failed: {e}")
        traceback.print_exc()
        return False

def test_yfinance_fetch():
    """Test fetching market data"""
    print("\nTesting yfinance data fetch...")
    try:
        import yfinance as yf

        # Try to fetch a simple ticker (Reliance for Indian market test)
        ticker = yf.Ticker("RELIANCE.NS")
        hist = ticker.history(period="1d")

        if not hist.empty:
            print(f"[PASS] Successfully fetched RELIANCE.NS data")
            print(f"  Last close: Rs.{hist['Close'].iloc[-1]:.2f}")
            return True
        else:
            print("[FAIL] No data returned (might be market closed)")
            return False
    except Exception as e:
        print(f"[FAIL] yfinance fetch failed: {e}")
        return False

def test_sentiment_analyzer():
    """Test sentiment analyzer if available"""
    print("\nTesting sentiment analyzer...")
    try:
        from utils.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze_text("This stock is performing great!")
        print(f"[PASS] Sentiment analyzer working")
        print(f"  Sample result: {result}")
        return True
    except ImportError:
        print("[WARN] Sentiment analyzer not available (vaderSentiment not installed)")
        return False
    except Exception as e:
        print(f"[FAIL] Sentiment analyzer failed: {e}")
        return False

def test_dashboard_syntax():
    """Test dashboard.py for syntax errors"""
    print("\nTesting dashboard.py syntax...")
    try:
        import py_compile
        py_compile.compile("dashboard.py", doraise=True)
        print("[PASS] dashboard.py has no syntax errors")
        return True
    except py_compile.PyCompileError as e:
        print(f"[FAIL] dashboard.py has syntax errors: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Could not test dashboard: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("SmartTrader Quick Test Suite")
    print("=" * 60)

    all_passed = True

    # Test imports
    import_results = test_imports()
    print("\nImport Results:")
    for package, result in import_results.items():
        status = "[PASS]" if "OK" in result else "[FAIL]"
        print(f"  {status} {package}: {result}")
        if "FAIL" in result:
            all_passed = False

    # Test config
    if not test_config():
        all_passed = False

    # Test yfinance
    if not test_yfinance_fetch():
        all_passed = False

    # Test sentiment analyzer
    test_sentiment_analyzer()  # Don't fail overall if this fails

    # Test dashboard syntax
    if not test_dashboard_syntax():
        all_passed = False

    # Final result
    print("\n" + "=" * 60)
    if all_passed:
        print("[PASS] All core tests passed! SmartTrader is ready to use.")
        print("\nNext steps:")
        print("  1. Run: streamlit run dashboard.py")
        print("  2. Or use: run.bat (Windows)")
    else:
        print("[FAIL] Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("  1. Install missing packages: pip install <package_name>")
        print("  2. Check SETUP_GUIDE.md for detailed setup")
        print("  3. Verify .env file has correct API keys")
    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
