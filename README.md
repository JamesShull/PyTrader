# PyTrader

PyTrader is a tool for interacting with the Alpaca trading API. It now features a web-based user interface, alongside its original Textual User Interface (TUI) and direct CLI commands.

## Features

*   **Web UI (New!):**
    *   View account information (equity, buying power, etc.).
    *   Display current positions with market values and P/L.
    *   Place trade orders (buy/sell, various order types).
*   **TUI Mode:** An interactive terminal application for navigating features (account info, quotes).
*   **CLI Mode:** Direct commands for quick actions (e.g., getting quotes).
*   **Account Information:** Access Alpaca trading account status.
*   **Stock Quotes & Positions:** Fetch and display real-time stock quotes and current positions.
*   **Watchlist (TUI):** Load a list of symbols from a `watch.json` file or specify symbols directly for the TUI.

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

### Running the Web UI Application

The Web UI provides a modern interface for account overview, positions, and trading.

1.  **Start the FastAPI Backend:**
    *   Ensure your virtual environment is activated and API keys are set in `.env`.
    *   From the project root directory (`PyTrader/`):
        ```bash
        uvicorn src.api:app --reload
        ```
    *   The backend API will typically be available at `http://127.0.0.1:8000`. You can access the API documentation at `http://127.0.0.1:8000/docs`.

2.  **Start the Svelte Frontend:**
    *   Open a new terminal.
    *   Navigate to the `frontend` directory:
        ```bash
        cd frontend
        ```
    *   Install frontend dependencies (if you haven't already or if `package.json` changed):
        ```bash
        npm install
        # or yarn install, or pnpm install
        ```
    *   Start the Svelte development server:
        ```bash
        npm run dev
        ```
    *   The frontend will typically be available at `http://localhost:5173`. Open this address in your web browser.

### Running the TUI Application (Legacy)

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
