import os

import alpaca_trade_api as tradeapi
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
        except Exception as e:
            return {"error": f"Failed to fetch account info: {e}"}

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
        except Exception as e:
            return {"error": f"Failed to fetch quotes: {e}"}


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
