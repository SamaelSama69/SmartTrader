# SmartTrader Tests

This directory contains unit tests for the SmartTrader project.

## Requirements

Install pytest:
```bash
pip install pytest
```

## Running Tests

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run a specific test file:
```bash
pytest tests/test_data_fetcher.py
```

Run a specific test class:
```bash
pytest tests/test_data_fetcher.py::TestMarketDataFetcher
```

Run a specific test:
```bash
pytest tests/test_data_fetcher.py::TestMarketDataFetcher::test_init
```

## Test Files

- `test_data_fetcher.py` - Tests for utils/data_fetcher.py
- `test_sentiment_analyzer.py` - Tests for utils/sentiment_analyzer.py
- `test_screener.py` - Tests for utils/screener.py

## Writing New Tests

1. Create a new file named `test_*.py` in this directory
2. Create test classes prefixed with `Test`
3. Create test methods prefixed with `test_`
4. Use fixtures from `conftest.py` as needed

Example:
```python
class TestMyModule:
    def test_something(self):
        assert True
```

## Notes

- Tests use the `utils/validators.py` module for input validation
- Some tests may be skipped if API keys are not configured
- Network-dependent tests will fail gracefully if offline
