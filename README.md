# PyTrader

PyTrader is a command-line tool for interacting with the Alpaca trading API. It provides both a Textual User Interface (TUI) for an interactive experience and direct CLI commands for specific actions like fetching stock quotes.

## Features

*   **Account Information:** View your Alpaca trading account status, equity, buying power, etc.
*   **Stock Quotes:** Fetch and display real-time stock quotes.
*   **Watchlist:** Load a list of symbols from a `watch.json` file or specify symbols directly.
*   **TUI Mode:** An interactive terminal application for navigating features.
*   **CLI Mode:** Direct commands for quick actions (e.g., getting quotes).

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd PyTrader
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.\.venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Alpaca API Keys:**
    *   Copy the `.env.example` file to `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and add your Alpaca API Key ID and Secret Key:
        ```
        APCA_API_KEY_ID="YOUR_KEY_ID"
        APCA_API_SECRET_KEY="YOUR_SECRET_KEY"
        # APCA_API_BASE_URL="https://paper-api.alpaca.markets" # Optional: defaults to paper trading
        ```
        Ensure you are using paper trading keys if you are testing.

## Usage

### Running the TUI Application

The TUI provides an interactive way to view account information and stock quotes.

*   **Basic run (loads `watch.json` by default if it exists):**
    ```bash
    python src/main.py run-tui
    ```

*   **Specify symbols directly:**
    ```bash
    python src/main.py run-tui --symbol AAPL,MSFT
    ```
    (or `python src/main.py run-tui -s AAPL,MSFT`)

*   **Specify a custom watchlist file:**
    ```bash
    python src/main.py run-tui --watchlist /path/to/your/custom_watchlist.json
    ```
    (or `python src/main.py run-tui -w /path/to/your/custom_watchlist.json`)

    The `watch.json` file should be a simple JSON array of strings:
    ```json
    [
        "DIA",
        "SPY",
        "QQQ"
    ]
    ```

**TUI Keybindings:**

*   `q`: Quit
*   `d`: Toggle Dark Mode
*   `v`: View Account Information
*   `r`: View/Refresh Quotes from Watchlist
*   `p`: Place Order (Work In Progress)

### CLI Commands

#### Get Quotes

Fetch and display quotes for one or more symbols directly in your terminal.

*   **Fetch quotes for specified symbols:**
    ```bash
    python src/main.py get-quotes --symbols AAPL,GOOGL,TSLA
    ```
    (or `python src/main.py get-quotes -S AAPL,GOOGL,TSLA`)

    This will output a table with bid/ask prices and other quote details.

## Development

*   Run tests:
    ```bash
    make test
    ```
    (Ensure you have development dependencies installed, e.g., `pip install -r requirements-dev.txt` if such a file exists, or install `pytest` and `respx` manually).

Let’s try to trade programmatically
