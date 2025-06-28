import os

import alpaca_trade_api as tradeapi
import click
from colorama import Fore, Style
from colorama import init as colorama_init
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import Footer, Header, Label, Markdown, Static

# Initialize colorama
colorama_init(autoreset=True)

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv(
    "APCA_API_BASE_URL"
)  # Optional, defaults to paper trading if not set


class AlpacaService:
    """Handles Alpaca API interactions."""

    def __init__(self):
        self.api = None  # Initialize api to None
        self.error_message = None  # Initialize error_message to None

        if not API_KEY or not API_SECRET:
            self.error_message = "API keys not found. Please set APCA_API_KEY_ID and APCA_API_SECRET_KEY in your .env file."
            print(Fore.RED + self.error_message)
            # self.api remains None, self.error_message is set.
            return

        # Determine the effective base URL for connection attempts and logging
        effective_base_url = BASE_URL if BASE_URL else "https://paper-api.alpaca.markets"

        try:
            self.api = tradeapi.REST(API_KEY, API_SECRET, base_url=effective_base_url)
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


class TradeApp(App):
    """A Textual app for Alpaca Trading."""

    account_info = reactive(None)

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("v", "view_account", "View Account"),
        ("p", "place_order_screen", "Place Order"),
    ]

    CSS_PATH = "main.tcss"

    def __init__(self):
        super().__init__()
        self.alpaca_service = AlpacaService()
        self.account_info_widget_id = "account_info_display"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Container(
            Label("Welcome to Alpaca TUI Trader!", id="main_label"),
            Markdown("", id=self.account_info_widget_id),  # For displaying account info
            Static(
                "Press 'v' to view account, 'p' to place an order, 'q' to quit.",
                id="status_bar",
            ),
            id="main_container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        if self.alpaca_service.error_message:
            self.query_one("#main_label", Label).update(
                Fore.RED + self.alpaca_service.error_message
            )
            self.query_one(f"#{self.account_info_widget_id}", Markdown).update(
                Fore.RED
                + "Failed to initialize Alpaca Service. Check console for details."
            )
        else:
            self.query_one("#main_label", Label).update("Alpaca TUI Trader")
            self.action_view_account()  # Optionally load account info on startup

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark
        self.query_one("#status_bar", Static).update(
            f"Dark mode {'on' if self.dark else 'off'}"
        )

    def action_view_account(self) -> None:
        """Fetches and displays account information."""
        self.query_one("#status_bar", Static).update("Fetching account information...")
        account_data = self.alpaca_service.get_account_info()

        display_widget = self.query_one(f"#{self.account_info_widget_id}", Markdown)

        if account_data and "error" not in account_data:
            self.account_info = account_data  # Update reactive variable
            md_output = "## Account Information\n\n"
            for key, value in self.account_info.items():
                md_output += f"- **{key}:** {value}\n"
            display_widget.update(md_output)
            self.query_one("#status_bar", Static).update("Account information updated.")
            self.query_one("#main_label", Label).update("Account View")
        elif account_data and "error" in account_data:
            display_widget.update(Fore.RED + f"Error: {account_data['error']}")
            self.query_one("#status_bar", Static).update("Error fetching account info.")
        else:
            display_widget.update(
                Fore.RED
                + "Error: Could not fetch account information. API might be down or keys invalid."
            )
            self.query_one("#status_bar", Static).update("Error fetching account info.")

    def action_place_order_screen(self) -> None:
        """Placeholder for switching to an order placement screen."""
        # This would typically push a new Screen in Textual
        self.query_one(f"#{self.account_info_widget_id}", Markdown).update(
            ""
        )  # Clear previous content
        self.query_one("#main_label", Label).update(
            Fore.YELLOW + "Order Placement [WIP]"
        )
        self.query_one("#status_bar", Static).update(
            "Switched to Order Placement View (Work In Progress)"
        )
        # Example: self.push_screen(OrderScreen())
        print(
            Fore.YELLOW + Style.BRIGHT + "Order placement screen not yet implemented."
        )


@click.group()
def cli():
    """Alpaca TUI Trader CLI"""
    pass


@cli.command()
def run_tui():  # Renamed from 'run' to avoid conflict with Makefile target if main.py is called directly
    """Run the TUI application."""
    app = TradeApp()
    app.run()
    print(Style.RESET_ALL)  # Reset colors when app exits


@cli.command()
@click.option("--symbol", default="AAPL", help="Stock symbol to check.")
def check_price(symbol: str):
    """Placeholder to check stock price (uses colorama)."""
    # This is a non-TUI command, just for demonstrating click and colorama
    # In a real app, price checking would be part of the TUI or Alpaca integration
    print(Fore.GREEN + f"Checking price for {symbol}...")
    print(
        Fore.BLUE
        + Style.BRIGHT
        + f"Price of {symbol}: $150.00 (dummy data)"
        + Style.RESET_ALL
    )


if __name__ == "__main__":
    cli()
