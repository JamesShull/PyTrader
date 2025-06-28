import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
import os

# Set dummy env vars for testing if not already set, to avoid AlpacaService errors during import
os.environ.setdefault("APCA_API_KEY_ID", "dummy_test_key")
os.environ.setdefault("APCA_API_SECRET_KEY", "dummy_test_secret")
os.environ.setdefault("APCA_API_BASE_URL", "http://dummy.test.url")

from src.main import cli, TradeApp, AlpacaService # noqa: E402
from textual.widgets import Label, Markdown # noqa: E402
from textual.pilot import Pilot # noqa: E402


@pytest.fixture
def runner():
    return CliRunner()

def test_cli_entrypoint(runner: CliRunner):
    """Test the main CLI entry point."""
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "Alpaca TUI Trader CLI" in result.output

def test_check_price_command(runner: CliRunner):
    """Test the 'check-price' click command."""
    result = runner.invoke(cli, ["check-price", "--symbol", "TEST"])
    assert result.exit_code == 0
    assert "Checking price for TEST..." in result.output
    assert "Price of TEST: $150.00 (dummy data)" in result.output

# Textual App Tests
@pytest.mark.asyncio
async def test_trade_app_initial_state():
    """Test the initial state of the TradeApp."""
    # Mock AlpacaService to prevent real API calls during UI tests
    mock_alpaca_service = MagicMock(spec=AlpacaService)
    mock_alpaca_service.error_message = None # Simulate successful init
    mock_alpaca_service.get_account_info.return_value = {
        "Account Number": "TEST123ACC", "Status": "ACTIVE", "Equity": "$1,000.00"
    }

    with patch("src.main.AlpacaService", return_value=mock_alpaca_service):
        app = TradeApp()
        async with app.run_test() as pilot:
            assert app.title == "A Textual app for Alpaca Trading." # Default title

            # Check initial label (might be updated by on_mount's call to action_view_account)
            main_label = pilot.app.query_one("#main_label", Label)
            # Depending on on_mount logic, this could be "Account View" or the initial error/welcome
            # If action_view_account is called on_mount and is successful:
            assert main_label.renderable == "Account View" or main_label.renderable == "Alpaca TUI Trader"

            status_bar = pilot.app.query_one("#status_bar")
            assert "Press 'v' to view account" in str(status_bar.renderable) # Initial status

            # Verify that get_account_info was called if it's part of on_mount
            if "Account View" in str(main_label.renderable): # Indicates on_mount called view_account
                 mock_alpaca_service.get_account_info.assert_called_once()


@pytest.mark.asyncio
async def test_trade_app_toggle_dark_mode():
    """Test toggling dark mode."""
    with patch("src.main.AlpacaService") as mock_service_class:
        mock_service_class.return_value.error_message = None
        app = TradeApp()
        async with app.run_test() as pilot:
            initial_dark_mode = app.dark
            await pilot.press("d")
            assert app.dark is not initial_dark_mode
            await pilot.press("d")
            assert app.dark is initial_dark_mode
            status_bar = pilot.app.query_one("#status_bar")
            assert f"Dark mode {'on' if app.dark else 'off'}" in str(status_bar.renderable)

@pytest.mark.asyncio
async def test_trade_app_view_account_action():
    """Test the view account action."""
    mock_alpaca_service = MagicMock(spec=AlpacaService)
    mock_alpaca_service.error_message = None
    mock_account_details = {
        "Account Number": "ACC123", "Status": "ACTIVE", "Equity": "$500.00",
        "Buying Power": "$1000.00", "Cash": "$500.00",
        "Portfolio Value": "$500.00", "Daytrade Count": 0, "Currency": "USD"
    }
    mock_alpaca_service.get_account_info.return_value = mock_account_details

    with patch("src.main.AlpacaService", return_value=mock_alpaca_service):
        app = TradeApp()
        async with app.run_test() as pilot:
            # App might call view_account on_mount, reset mock if so for this specific test
            mock_alpaca_service.get_account_info.reset_mock()

            await pilot.press("v") # Trigger the action

            mock_alpaca_service.get_account_info.assert_called_once()

            account_display = pilot.app.query_one(f"#{app.account_info_widget_id}", Markdown)
            rendered_markdown = account_display.document.text

            assert "## Account Information" in rendered_markdown
            assert "ACC123" in rendered_markdown
            assert "$500.00" in rendered_markdown

            main_label = pilot.app.query_one("#main_label", Label)
            assert main_label.renderable == "Account View"

@pytest.mark.asyncio
async def test_trade_app_view_account_action_api_error():
    """Test the view account action when AlpacaService returns an error."""
    mock_alpaca_service = MagicMock(spec=AlpacaService)
    mock_alpaca_service.error_message = None # Service itself initialized fine
    error_response = {"error": "Failed to connect to API (mocked error)"}
    mock_alpaca_service.get_account_info.return_value = error_response

    with patch("src.main.AlpacaService", return_value=mock_alpaca_service):
        app = TradeApp()
        async with app.run_test() as pilot:
            mock_alpaca_service.get_account_info.reset_mock() # Reset from potential on_mount call

            await pilot.press("v") # Trigger action

            mock_alpaca_service.get_account_info.assert_called_once()

            account_display = pilot.app.query_one(f"#{app.account_info_widget_id}", Markdown)
            rendered_markdown = account_display.document.text
            assert "Error: Failed to connect to API (mocked error)" in rendered_markdown

            status_bar = pilot.app.query_one("#status_bar")
            assert "Error fetching account info" in str(status_bar.renderable)


@pytest.mark.asyncio
async def test_trade_app_quit_action():
    """Test the quit action."""
    with patch("src.main.AlpacaService") as mock_service_class:
        mock_service_class.return_value.error_message = None
        app = TradeApp()
        async with app.run_test() as pilot:
            await pilot.press("q")
            # The app.run_test() context manager handles the exit signal.
            # We just need to ensure the key press doesn't cause an error.
            # Actual exit is tested by textual's own mechanisms.
            pass

# To run these tests: pytest tests/test_main.py
# Ensure you have pytest and pytest-asyncio installed.
# Also, ensure .env or dummy env vars are correctly set up so AlpacaService can initialize.
# The patch for AlpacaService is crucial for UI tests to avoid real network calls.
#
# Note on `app.run_test()`:
# It provides a `Pilot` object which allows you to interact with the app.
# The context manager (`async with`) handles starting and stopping the app for the test.
#
# Testing Click's run_tui command directly is a bit more involved
# as it calls app.run() which blocks. For that, you'd typically mock
# TradeApp itself or its run method.
# For example:
# @patch('src.main.TradeApp.run')
# def test_run_tui_command(mock_app_run, runner):
#     result = runner.invoke(cli, ["run-tui"])
#     assert result.exit_code == 0
#     mock_app_run.assert_called_once()
#
# However, testing the app's behavior via textual.pilot is more thorough for the TUI parts.
#
# The dummy env vars at the top are a simple way to ensure AlpacaService
# doesn't immediately fail on import if no .env is present during test discovery.
# More robust solutions might involve a session-scoped fixture to manage this.
#
# The `noqa: E402` comments are because we're setting environment variables
# before some imports, which is necessary for the AlpacaService initialization logic
# but goes against strict linting of "imports at top of file".
# This is a common pattern in tests that need to manipulate environment for modules.
