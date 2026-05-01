# Contributing to SmartTrader

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/SmartTrader.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
5. Install dependencies: `pip install -r requirements.txt`
6. Copy `.env.example` to `.env` and fill in your API keys
7. Run tests: `pytest tests/ -v`

## Code Standards

- **Style**: Black with 127 character line length
- **Linting**: Flake8
- **Type Checking**: MyPy (where possible)
- **Tests**: Pytest with 80%+ coverage

## Making Changes

1. Create a new branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Run tests: `pytest tests/ -v`
4. Run linters: `flake8 .` and `black --check .`
5. Commit: `git commit -m "Add feature X"`
6. Push: `git push origin feature/my-feature`
7. Create a Pull Request

## Pull Request Guidelines

- Describe what the PR does
- Link any related issues
- Ensure all tests pass
- Ensure coverage remains above 80%
- Add tests for new features