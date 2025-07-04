import os
import time

import alpaca_trade_api as tradeapi
from ratelimit import limits, RateLimitException
import click
from colorama import Fore, Style
from colorama import init as colorama_init
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Footer, Header, Label, Markdown, Static, DataTable

# Initialize colorama
colorama_init(autoreset=True)

# Load environment variables from .env file
load_dotenv()

# API_KEY = os.getenv("APCA_API_KEY_ID") # Will be read in AlpacaService.__init__
# API_SECRET = os.getenv("APCA_API_SECRET_KEY") # Will be read in AlpacaService.__init__
# BASE_URL = os.getenv("APCA_API_BASE_URL") # Will be read in AlpacaService.__init__

# Define rate limits
# Alpaca: 200 requests per minute, burst of 10 requests per second.
# We'll use two decorators to handle this.
# The library handles them in order, so the stricter per-second limit will be checked first.
CALLS_PER_SECOND = 10
PERIOD_PER_SECOND = 1  # 1 second

CALLS_PER_MINUTE = 200
PERIOD_PER_MINUTE = 60  # 60 seconds


class AlpacaService:
    """Handles Alpaca API interactions."""

    def __init__(self):
        self.api = None  # Initialize api to None
        self.error_message = None  # Initialize error_message to None

        # Read environment variables inside __init__ to be responsive to monkeypatching in tests
        api_key = os.getenv("APCA_API_KEY_ID")
        api_secret = os.getenv("APCA_API_SECRET_KEY")
        base_url_env = os.getenv("APCA_API_BASE_URL")

        if not api_key or not api_secret:
            self.error_message = "API keys not found. Please set APCA_API_KEY_ID and APCA_API_SECRET_KEY in your .env file."
            print(Fore.RED + self.error_message)
            # self.api remains None, self.error_message is set.
            return

        # Determine the effective base URL for connection attempts and logging
        effective_base_url = base_url_env if base_url_env else "https://paper-api.alpaca.markets"

        try:
            self.api = tradeapi.REST(api_key, api_secret, base_url=effective_base_url)
            self.api.get_account()  # Test connection
            # If successful, self.error_message remains None (or explicitly set it if preferred)
            print(Fore.GREEN + f"Successfully connected to Alpaca API at {effective_base_url}.")
        except Exception as e:
            self.api = None # Ensure api is None on connection failure
            self.error_message = f"Failed to connect to Alpaca API at {effective_base_url}: {e}"
            print(Fore.RED + self.error_message)

    @limits(calls=CALLS_PER_SECOND, period=PERIOD_PER_SECOND)
    @limits(calls=CALLS_PER_MINUTE, period=PERIOD_PER_MINUTE)
    def get_account_info(self):
        # Prioritize checking if initialization itself failed
        if self.error_message and not self.api:
            return {"error": self.error_message}
        # If api is somehow not set, but no init error (should be rare with current logic)
        if not self.api:
            return {"error": "API not initialized (unknown reason)."}
        try:
            account = self.api.get_account()
            return {
                "Account Number": account.account_number,
                "Status": account.status,
                "Equity": f"${float(account.equity):,.2f}",
                "Buying Power": f"${float(account.buying_power):,.2f}",
                "Cash": f"${float(account.cash):,.2f}",
                "Portfolio Value": f"${float(account.portfolio_value):,.2f}",
                "Daytrade Count": account.daytrade_count,
                "Currency": account.currency,
            }
        except RateLimitException as rle:
            # Wait for the remaining period and retry, or just return an error
            # For now, let's return an error. A more sophisticated approach might retry.
            # The `ratelimit` library sleeps by default if `raise_on_limit` is False,
            # but we are using the default `raise_on_limit=True`.
            return {"error": f"Rate limit exceeded for get_account_info: {rle}. Please try again shortly."}
        except Exception as e:
            return {"error": f"Failed to fetch account info: {e}"}

    @limits(calls=CALLS_PER_SECOND, period=PERIOD_PER_SECOND)
    @limits(calls=CALLS_PER_MINUTE, period=PERIOD_PER_MINUTE)
    def get_quotes(self, symbols: list[str]):
        """Fetches the latest quotes for a list of symbols."""
        if self.error_message and not self.api:
            return {"error": self.error_message}
        if not self.api:
            return {"error": "API not initialized."}
        if not symbols:
            return {}  # Return empty dict if no symbols provided

        try:
            # Use get_latest_quotes for multiple symbols
            # Note: The SDK's get_latest_quotes might return a dictionary where keys are symbols
            # and values are quote objects.
            quote_data = self.api.get_latest_quotes(symbols)

            # Process the quote data into a more consistent format if needed
            # For example, converting quote objects to dictionaries
            processed_quotes = {}
            for symbol, quote in quote_data.items():
                processed_quotes[symbol] = {
                    "ask_price": quote.ap,
                    "bid_price": quote.bp,
                    "ask_size": quote.as_, # .as is a keyword
                    "bid_size": quote.bs,
                    "timestamp": quote.t.isoformat() if quote.t else None,
                }
            return processed_quotes
        except RateLimitException as rle:
            return {"error": f"Rate limit exceeded for get_quotes: {rle}. Please try again shortly."}
        except Exception as e:
            return {"error": f"Failed to fetch quotes: {e}"}

    @limits(calls=CALLS_PER_SECOND, period=PERIOD_PER_SECOND)
    @limits(calls=CALLS_PER_MINUTE, period=PERIOD_PER_MINUTE)
    def list_positions(self):
        """Fetches current positions and their market values."""
        if self.error_message and not self.api:
            return {"error": self.error_message}
        if not self.api:
            return {"error": "API not initialized."}

        try:
            positions = self.api.list_positions()
            if not positions:
                return [] # Return empty list if no positions

            # Extract symbols to fetch quotes for all positions at once
            symbols = [position.symbol for position in positions]
            # quotes_data = self.get_quotes(symbols) # This calls the rate-limited get_quotes

            # Use a non-rate-limited internal call or handle potential nested rate limit issues carefully.
            # For simplicity, let's assume direct SDK call for latest trade is acceptable here,
            # or that get_quotes is designed to be called internally.
            # To avoid complex rate limit handling within a single method, we'll fetch latest trade for each.
            # A more optimized approach might involve a bulk quote fetch if available and not hitting limits.

            enriched_positions = []
            for pos in positions:
                current_price = pos.current_price # Already provided by list_positions
                market_value = float(pos.market_value)
                unrealized_pl = float(pos.unrealized_pl)
                enriched_positions.append(
                    {
                        "symbol": pos.symbol,
                        "qty": float(pos.qty),
                        "avg_entry_price": float(pos.avg_entry_price),
                        "current_price": float(current_price) if current_price else None,
                        "market_value": market_value,
                        "unrealized_pl": unrealized_pl,
                        "unrealized_plpc": float(pos.unrealized_plpc) * 100, # percentage
                        "asset_class": pos.asset_class,
                        "exchange": pos.exchange,
                    }
                )
            return enriched_positions
        except RateLimitException as rle:
            return {"error": f"Rate limit exceeded for list_positions: {rle}. Please try again shortly."}
        except Exception as e:
            return {"error": f"Failed to fetch positions: {e}"}

    @limits(calls=CALLS_PER_SECOND, period=PERIOD_PER_SECOND)
    @limits(calls=CALLS_PER_MINUTE, period=PERIOD_PER_MINUTE)
    def submit_trade_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        order_type: str,
        time_in_force: str,
        limit_price: float | None = None,
        stop_price: float | None = None,
        client_order_id: str | None = None, # Optional client order ID
    ):
        """Submits a trade order."""
        if self.error_message and not self.api:
            return {"error": self.error_message}
        if not self.api:
            return {"error": "API not initialized."}

        # Validate inputs (basic)
        if not symbol or not isinstance(symbol, str):
            return {"error": "Invalid symbol."}
        if not isinstance(qty, (int, float)) or qty <= 0:
            return {"error": "Invalid quantity."}
        if side not in ["buy", "sell"]:
            return {"error": "Invalid side. Must be 'buy' or 'sell'."}
        if order_type not in ["market", "limit", "stop", "stop_limit", "trailing_stop"]:
            return {"error": "Invalid order type."}
        if time_in_force not in ["day", "gtc", "opg", "cls", "ioc", "fok"]:
            return {"error": "Invalid time in force."}

        if order_type in ["limit", "stop_limit"] and limit_price is None:
            return {"error": "Limit price is required for limit and stop_limit orders."}
        if order_type in ["stop", "stop_limit", "trailing_stop"] and stop_price is None and order_type != "trailing_stop": # trailing_stop might use trail_percent/trail_price
             # AlpacaPy might handle trailing stop params differently, this is a basic check
            if order_type != "trailing_stop": # More specific check for non-trailing stops
                return {"error": "Stop price is required for stop and stop_limit orders."}


        try:
            order_params = {
                "symbol": symbol.upper(),
                "qty": qty,
                "side": side,
                "type": order_type,
                "time_in_force": time_in_force,
            }
            if limit_price is not None:
                order_params["limit_price"] = limit_price
            if stop_price is not None: # This applies to stop, stop_limit. Trailing stop has trail_price or trail_percent
                order_params["stop_price"] = stop_price
            if client_order_id:
                order_params["client_order_id"] = client_order_id

            # For trailing_stop orders, specific parameters like trail_price or trail_percent are needed.
            # This example assumes they might be passed via stop_price or handled by SDK if None.
            # A more robust implementation would explicitly handle trail_percent/trail_price for trailing_stop.
            # e.g., if order_type == "trailing_stop": order_params["trail_percent"] = X or order_params["trail_price"] = Y

            order = self.api.submit_order(**order_params)
            return {
                "id": order.id,
                "client_order_id": order.client_order_id,
                "symbol": order.symbol,
                "qty": float(order.qty),
                "side": order.side,
                "type": order.type,
                "time_in_force": order.time_in_force,
                "status": order.status,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "limit_price": float(order.limit_price) if order.limit_price else None,
                "stop_price": float(order.stop_price) if order.stop_price else None,
            }
        except RateLimitException as rle:
            return {"error": f"Rate limit exceeded for submit_trade_order: {rle}. Please try again shortly."}
        except tradeapi.rest.APIError as apie:
            # Catch specific Alpaca API errors for better feedback
            return {"error": f"Alpaca API error: {apie.message} (Code: {apie.code})", "raw_error": str(apie)}
        except Exception as e:
            return {"error": f"Failed to submit order: {e}", "raw_error": str(e)}


class TradeApp(App):
    """A Textual app for Alpaca Trading."""

    account_info = reactive(None)
    quotes_data = reactive(dict()) # Using dict to store quotes by symbol

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("v", "view_account", "View Account"),
        ("p", "place_order_screen", "Place Order"),
        ("r", "refresh_quotes", "Refresh Quotes"), # New binding
    ]

    CSS_PATH = "main.tcss"

    def __init__(self, initial_symbols: list[str] = None): # Accept initial symbols
        super().__init__()
        self.alpaca_service = AlpacaService()
        self.account_info_widget_id = "account_info_display"
        self.quotes_table_id = "quotes_table"
        self.initial_symbols = initial_symbols if initial_symbols else []

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Container(
            Label("Welcome to Alpaca TUI Trader!", id="main_label"),
            Markdown("", id=self.account_info_widget_id),  # For displaying account info
            DataTable(id=self.quotes_table_id), # Added DataTable
            Static(
                "Press 'v' to view account, 'r' for quotes, 'p' for order, 'q' to quit.",
                id="status_bar",
            ),
            id="main_container",
        )
        yield Footer()

    async def on_mount(self) -> None: # Made on_mount async
        """Called when app starts."""
        # Initialize quotes table
        table = self.query_one(f"#{self.quotes_table_id}", DataTable)
        table.add_columns("Symbol", "Bid", "Ask", "Buy", "Sell")
        table.visible = False # Initially hide until data is loaded or view is switched

        if self.alpaca_service.error_message:
            self.query_one("#main_label", Label).update(
                Fore.RED + self.alpaca_service.error_message
            )
            self.query_one(f"#{self.account_info_widget_id}", Markdown).update(
                Fore.RED
                + "Failed to initialize Alpaca Service. Check console for details."
            )
            self.query_one("#status_bar", Static).update(f"Status: {self.alpaca_service.error_message}")
        else:
            self.query_one("#main_label", Label).update("Alpaca TUI Trader")
            # Load initial data if symbols are provided
            if self.initial_symbols:
                await self.action_refresh_quotes() # Call the new quote refresh action
            else: # Default to account view if no symbols
                self.action_view_account()


    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark
        self.query_one("#status_bar", Static).update(
            f"Dark mode {'on' if self.dark else 'off'}"
        )

    async def action_refresh_quotes(self) -> None:
        """Fetches and displays stock quotes for symbols in initial_symbols."""
        self.query_one(f"#{self.account_info_widget_id}", Markdown).visible = False
        quotes_table = self.query_one(f"#{self.quotes_table_id}", DataTable)
        quotes_table.visible = True
        quotes_table.loading = True
        quotes_table.clear() # Clear previous rows
        self.query_one("#status_bar", Static).update(f"Fetching quotes for: {', '.join(self.initial_symbols)}...")

        if not self.initial_symbols:
            self.query_one("#status_bar", Static).update("No symbols to fetch quotes for. Update watchlist or provide symbols.")
            self.query_one("#main_label", Label).update("Quotes View [No Symbols]")
            quotes_table.loading = False
            quotes_table.add_row("No symbols configured.", "", "", "", "")
            return

        fetched_data = self.alpaca_service.get_quotes(self.initial_symbols)
        quotes_table.loading = False

        if fetched_data and "error" not in fetched_data:
            self.quotes_data = fetched_data # Update reactive variable
            rows = []
            for symbol, data in self.quotes_data.items():
                bid_price = data.get('bid_price', 'N/A')
                ask_price = data.get('ask_price', 'N/A')
                # Ensure prices are formatted to 2 decimal places if they are numbers
                bid_str = f"{bid_price:.2f}" if isinstance(bid_price, (int, float)) else str(bid_price)
                ask_str = f"{ask_price:.2f}" if isinstance(ask_price, (int, float)) else str(ask_price)
                rows.append((symbol, bid_str, ask_str, "Buy", "Sell"))

            if rows:
                for row in rows:
                    quotes_table.add_row(*row, key=row[0]) # Use symbol as key
            else:
                quotes_table.add_row("No quote data found for symbols.", "", "", "", "")
            self.query_one("#status_bar", Static).update("Quotes updated.")
            self.query_one("#main_label", Label).update("Quotes View")
        elif fetched_data and "error" in fetched_data:
            error_msg = fetched_data['error']
            self.query_one("#status_bar", Static).update(f"Error fetching quotes: {error_msg}")
            self.query_one("#main_label", Label).update("Quotes View [Error]")
            quotes_table.add_row(f"Error: {error_msg}", "", "", "", "")
        else:
            self.query_one("#status_bar", Static).update("Error: Could not fetch quotes. Check connection or symbols.")
            self.query_one("#main_label", Label).update("Quotes View [Error]")
            quotes_table.add_row("Unknown error fetching quotes.", "", "", "", "")


    def action_view_account(self) -> None:
        """Fetches and displays account information."""
        self.query_one(f"#{self.quotes_table_id}", DataTable).visible = False # Hide quotes table
        account_display = self.query_one(f"#{self.account_info_widget_id}", Markdown)
        account_display.visible = True # Show account info
        self.query_one("#status_bar", Static).update("Fetching account information...")
        account_data = self.alpaca_service.get_account_info()

        if account_data and "error" not in account_data:
            self.account_info = account_data
            md_output = "## Account Information\n\n"
            for key, value in self.account_info.items():
                md_output += f"- **{key}:** {value}\n"
            account_display.update(md_output)
            self.query_one("#status_bar", Static).update("Account information updated.")
            self.query_one("#main_label", Label).update("Account View")
        elif account_data and "error" in account_data:
            account_display.update(Fore.RED + f"Error: {account_data['error']}")
            self.query_one("#status_bar", Static).update("Error fetching account info.")
        else:
            account_display.update(
                Fore.RED
                + "Error: Could not fetch account information. API might be down or keys invalid."
            )
            self.query_one("#status_bar", Static).update("Error fetching account info.")

    def action_place_order_screen(self) -> None:
        """Placeholder for switching to an order placement screen."""
        self.query_one(f"#{self.quotes_table_id}", DataTable).visible = False # Hide quotes
        self.query_one(f"#{self.account_info_widget_id}", Markdown).visible = False # Hide account
        self.query_one(f"#{self.account_info_widget_id}", Markdown).update(
            ""
        )
        self.query_one("#main_label", Label).update(
            Fore.YELLOW + "Order Placement [WIP]"
        )
        self.query_one("#status_bar", Static).update(
            "Switched to Order Placement View (Work In Progress)"
        )
        print(
            Fore.YELLOW + Style.BRIGHT + "Order placement screen not yet implemented."
        )


import json # Add json import for reading watchlist

@click.group()
def cli():
    """Alpaca TUI Trader CLI"""
    pass


# Define a simple strategy (e.g., Buy and Hold or SMA Crossover)
# Moved to module level to be importable by tests
import backtrader as bt # backtrader needs to be imported here for the class definition

class SimpleSMAStrategy(bt.Strategy):
    params = (('sma_period', 20),)

    def __init__(self):
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.p.sma_period
        )
        # To avoid "array assignment index out of range" if data is too short for period
        self.dataclose = self.datas[0].close

    def next(self):
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            if len(self.sma.lines.sma) > 0 and self.dataclose[0] > self.sma[0]: # Ensure SMA has calculated values
                # BUY, BUY, BUY!!! (with default parameters)
                # self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.buy()
        else:
            if len(self.sma.lines.sma) > 0 and self.dataclose[0] < self.sma[0]: # Ensure SMA has calculated values
                # SELL, SELL, SELL!!! (with all parameters)
                # self.log('SELL CREATE, %.2f' % self.dataclose[0])
                self.sell()


@cli.command()
@click.option("--start-date", type=str, required=True, help="Start date for backtesting (YYYY-MM-DD).")
@click.option("--end-date", type=str, required=True, help="End date for backtesting (YYYY-MM-DD).")
@click.option("--symbol", type=str, required=True, help="Stock symbol to backtest (e.g., AAPL).")
def backtest(start_date: str, end_date: str, symbol: str):
    """Run a simple backtest for a given stock and date range."""
    global SimpleSMAStrategy # Explicitly state we are using the global/module-level class
    from datetime import datetime # bt is already imported at module level

    # Create a Cerebro entity
    cerebro = bt.Cerebro()

    # Datasource (example: Yahoo Finance)
    # Note: Alpaca data feed would be more appropriate if available and integrated with backtrader
    # For simplicity, this example might use YahooFinanceData if directly usable
    # or expect a CSV file. Let's try with Alpaca's historical data if possible,
    # otherwise, we might need to adjust data fetching.

    # For now, let's assume we have a way to get data into backtrader's format.
    # This part will likely need adjustment based on how Alpaca data is fed.
    # Example: Fetching data using Alpaca API and converting to pandas DataFrame
    # then feeding it to Backtrader.

    alpaca_service = AlpacaService()
    if alpaca_service.error_message and not alpaca_service.api:
        print(Fore.RED + f"Error: {alpaca_service.error_message}")
        return

    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print(Fore.RED + "Error: Invalid date format. Please use YYYY-MM-DD.")
        return

    print(Fore.CYAN + f"Fetching historical data for {symbol} from {start_date} to {end_date}...")

    try:
        # Correctly call get_bars method
        bars = alpaca_service.api.get_bars(symbol, tradeapi.TimeFrame.Day, start_date, end_date).df
        # Ensure columns are named as expected by Backtrader: open, high, low, close, volume
        bars = bars.rename(columns={
            'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close', 'v': 'volume'
        })
        # Backtrader expects datetime index to be timezone naive for pandas df
        if bars.empty:
            print(Fore.YELLOW + f"No data found for {symbol} in the given date range.")
            return

        if bars.index.tz is not None:
            bars.index = bars.index.tz_localize(None)

        # Ensure enough data for the SMA period
        if len(bars) < SimpleSMAStrategy.params.sma_period:
            print(Fore.YELLOW + f"Not enough data ({len(bars)} bars) for SMA period ({SimpleSMAStrategy.params.sma_period}). Skipping backtest.")
            return

        data_feed = bt.feeds.PandasData(dataname=bars)
        cerebro.adddata(data_feed)
    except Exception as e:
        print(Fore.RED + f"Error fetching or processing data for {symbol}: {e}")
        return


    # Define a simple strategy (e.g., Buy and Hold or SMA Crossover)
    class SimpleSMAStrategy(bt.Strategy):
        params = (('sma_period', 20),)

        def __init__(self):
            self.sma = bt.indicators.SimpleMovingAverage(
                self.datas[0], period=self.p.sma_period
            )

        def next(self):
            # Simple buy if close is above SMA
            if not self.position: # Not in the market
                if self.datas[0].close > self.sma:
                    self.buy()
            # Simple sell if close is below SMA
            elif self.datas[0].close < self.sma:
                self.sell()

    cerebro.addstrategy(SimpleSMAStrategy)

    # Set initial cash
    cerebro.broker.setcash(100000.0)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
    cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')


    print(Fore.CYAN + "Running backtest...")
    results = cerebro.run()
    print(Fore.CYAN + "Backtest complete.")

    # Print out the final result
    final_value = cerebro.broker.getvalue()
    print(Fore.GREEN + f"Final Portfolio Value: ${final_value:,.2f}")

    # Print analysis results
    try:
        strategy_instance = results[0] # Get the first strategy instance (assuming one strategy)
        print("\n--- Strategy Analysis ---")
        # Check if sharpe ratio is NaN (can happen if no trades or std dev is zero)
        sharpe_ratio_analysis = strategy_instance.analyzers.sharpe_ratio.get_analysis()
        sharpe_ratio = sharpe_ratio_analysis.get('sharperatio', float('nan'))
        if sharpe_ratio is not None and not isinstance(sharpe_ratio, float) or sharpe_ratio != sharpe_ratio: # Check for NaN
             print(f"Sharpe Ratio: N/A (not enough data or trades)")
        else:
            print(f"Sharpe Ratio: {sharpe_ratio:.2f}")

        sqn_analysis = strategy_instance.analyzers.sqn.get_analysis()
        sqn_value = sqn_analysis.get('sqn', float('nan'))
        if sqn_value is not None and not isinstance(sqn_value, float) or sqn_value != sqn_value: # Check for NaN
            print(f"SQN: N/A")
        else:
            print(f"SQN: {sqn_value:.2f}")


        trade_analysis = strategy_instance.analyzers.trade_analyzer.get_analysis()
        if trade_analysis and trade_analysis.total.total > 0 : # Check if there are any trades
            print("\n--- Trade Analysis ---")
            print(f"Total Trades: {trade_analysis.total.total}")
            print(f"Winning Trades: {trade_analysis.won.total}")
            print(f"Losing Trades: {trade_analysis.lost.total}")
            if trade_analysis.won.total > 0:
                 print(f"Average Win: ${trade_analysis.won.pnl.average:,.2f}")
            if trade_analysis.lost.total > 0:
                print(f"Average Loss: ${trade_analysis.lost.pnl.average:,.2f}")
            print(f"Net PnL: ${trade_analysis.pnl.net.total:,.2f}")
        else:
            print("\nNo trades were executed or analyzable.")

    except Exception as e:
        print(Fore.RED + f"Error during analysis printing: {e}")

    # Optionally, plot the results if matplotlib is installed and a display is available
    # cerebro.plot() # This might require GUI, consider if suitable for CLI

    pass


@cli.command()
@click.option("--symbol", "-s", type=str, help="A single stock symbol to watch.")
@click.option("--watchlist", "-w", type=click.Path(exists=False, dir_okay=False), default="watch.json", help="Path to a JSON file with a list of stock symbols.")
def run_tui(symbol: str | None, watchlist: str):  # Renamed from 'run' to avoid conflict with Makefile target if main.py is called directly
    """Run the TUI application."""
    symbols_to_watch = []
    if symbol:
        symbols_to_watch = [s.strip().upper() for s in symbol.split(',')] # Allow comma-separated symbols
    elif os.path.exists(watchlist):
        try:
            with open(watchlist, 'r') as f:
                symbols_to_watch = json.load(f)
            if not isinstance(symbols_to_watch, list) or not all(isinstance(s, str) for s in symbols_to_watch):
                print(Fore.YELLOW + f"Warning: Watchlist file '{watchlist}' does not contain a valid list of strings. Ignoring.")
                symbols_to_watch = []
            else:
                symbols_to_watch = [s.strip().upper() for s in symbols_to_watch]
        except json.JSONDecodeError:
            print(Fore.RED + f"Error: Could not decode JSON from watchlist file '{watchlist}'.")
            symbols_to_watch = [] # Fallback to empty list
        except Exception as e:
            print(Fore.RED + f"Error reading watchlist file '{watchlist}': {e}")
            symbols_to_watch = [] # Fallback to empty list

    if not symbols_to_watch:
        print(Fore.YELLOW + "No symbols provided via --symbol or valid watch.json. TUI will start with an empty watchlist.")
        print(Fore.YELLOW + "You can create a 'watch.json' file with a list of symbols, e.g., [\"AAPL\", \"GOOG\"]")

    app = TradeApp(initial_symbols=symbols_to_watch)
    app.run()
    print(Style.RESET_ALL)  # Reset colors when app exits


from rich.table import Table # For formatted CLI output
from rich.console import Console # For rendering Rich content

@cli.command(name="get-quotes") # Renamed command
@click.option("--symbols", "-S", required=True, help="Comma-separated stock symbols to fetch quotes for (e.g., AAPL,MSFT).")
def get_quotes_cli(symbols: str):
    """Fetches and displays quotes for specified stock symbols (CLI, non-TUI)."""
    console = Console()
    alpaca_service = AlpacaService()

    if alpaca_service.error_message and not alpaca_service.api:
        console.print(f"[bold red]Error: {alpaca_service.error_message}[/bold red]")
        return

    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    if not symbol_list:
        console.print("[bold yellow]No symbols provided.[/bold yellow]")
        return

    console.print(f"[cyan]Fetching quotes for: {', '.join(symbol_list)}...[/cyan]")
    quotes_data = alpaca_service.get_quotes(symbol_list)

    if "error" in quotes_data:
        console.print(f"[bold red]API Error: {quotes_data['error']}[/bold red]")
        return

    if not quotes_data:
        console.print("[yellow]No quote data returned. Check symbols or API status.[/yellow]")
        return

    table = Table(title="Stock Quotes")
    table.add_column("Symbol", style="cyan", no_wrap=True)
    table.add_column("Bid Price", style="magenta")
    table.add_column("Ask Price", style="green")
    table.add_column("Bid Size", style="dim")
    table.add_column("Ask Size", style="dim")
    table.add_column("Timestamp (UTC)", style="yellow")

    for symbol, data in quotes_data.items():
        if "error" in data: # Should not happen with current get_quotes structure, but good for future
            table.add_row(symbol, f"[red]{data['error']}[/red]", "", "", "", "")
        else:
            bid_price = data.get('bid_price', 'N/A')
            ask_price = data.get('ask_price', 'N/A')
            bid_str = f"{bid_price:.2f}" if isinstance(bid_price, (int, float)) else str(bid_price)
            ask_str = f"{ask_price:.2f}" if isinstance(ask_price, (int, float)) else str(ask_price)

            table.add_row(
                symbol,
                bid_str,
                ask_str,
                str(data.get('bid_size', 'N/A')),
                str(data.get('ask_size', 'N/A')),
                str(data.get('timestamp', 'N/A')),
            )

    if not table.rows:
        console.print("[yellow]No data to display in table for the provided symbols.[/yellow]")
    else:
        console.print(table)


if __name__ == "__main__":
    cli()
