# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Dependencies
- `make setup` or `make install` - Create virtual environment and install all dependencies
- `make clean` - Remove virtual environment and cache files

### Code Quality
- `make lint` - Run ruff linter and formatter (auto-fixes issues)
- `make test` - Run pytest test suite

### Running the Application
- `make run` - Start the TUI application (equivalent to `python src/main.py run-tui`)
- `python src/main.py run-tui` - Run TUI with default watchlist (watch.json)
- `python src/main.py run-tui --symbol AAPL,MSFT` - Run TUI with specific symbols
- `python src/main.py get-quotes --symbols AAPL,GOOGL` - Get quotes via CLI (non-interactive)

### Single Test Execution
- `call .venv\Scripts\activate && pytest tests/test_main.py::test_specific_function` - Run specific test
- `call .venv\Scripts\activate && pytest tests/test_alpaca_service.py -v` - Run specific test file with verbose output

## Architecture Overview

### Core Components

**AlpacaService (src/main.py:24-106)**
- Handles all Alpaca API interactions
- Manages authentication using environment variables (APCA_API_KEY_ID, APCA_API_SECRET_KEY)
- Provides methods: `get_account_info()`, `get_quotes(symbols)`
- Gracefully handles connection failures and API errors

**TradeApp (src/main.py:108-268)**
- Textual-based TUI application with reactive state management
- Key bindings: 'v' (account), 'r' (quotes), 'p' (orders-WIP), 'q' (quit), 'd' (dark mode)
- Uses DataTable for quotes display and Markdown for account information
- Supports initial symbol loading from watchlist or command line

**CLI Interface (src/main.py:272-371)**
- Click-based command structure with two main commands:
  - `run-tui`: Interactive TUI mode
  - `get-quotes`: Direct CLI quote fetching with Rich table output

### Configuration Files

**Environment Setup**
- Requires `.env` file with Alpaca API credentials
- `watch.json` contains default symbol watchlist (JSON array of strings)
- `pyproject.toml` defines dependencies and tool configurations (ruff, pytest)

**Dependencies**
- Core: `click`, `textual`, `alpaca-trade-api`, `python-dotenv`, `colorama`
- Development: `pytest`, `pytest-cov`, `pytest-asyncio`, `respx`
- Code quality: `ruff` (linting and formatting)

### Key Design Patterns

**Error Handling Strategy**
- AlpacaService initialization gracefully handles missing credentials or connection failures
- All API methods return dictionaries with "error" keys on failure
- UI components check for error conditions before displaying data

**Reactive State Management**
- Uses Textual's reactive variables for account_info and quotes_data
- Async action methods for data fetching to prevent UI blocking
- Widget visibility toggling between account and quotes views

**Testing Architecture**
- Uses `respx` for mocking HTTP requests to Alpaca API
- Tests cover both successful responses and error conditions
- Environment variable mocking for testing different configuration scenarios

## Important Notes

- The application defaults to Alpaca's paper trading environment for safety
- Quote data includes bid/ask prices, sizes, and timestamps
- Order placement functionality is marked as "Work In Progress"
- Windows-specific Makefile commands (uses `call` and `Scripts\activate`)