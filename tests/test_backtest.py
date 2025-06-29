import pytest
from click.testing import CliRunner
from src.main import cli
from unittest.mock import patch, MagicMock
import pandas as pd
import backtrader as bt
from datetime import datetime

# Sample DataFrame to be returned by mock Alpaca API
# Expanded to 25 data points to satisfy SMA(20)
SAMPLE_BARS_DATA = {
    'o': [100 + i*0.1 for i in range(25)],
    'h': [105 + i*0.1 for i in range(25)],
    'l': [99 + i*0.1 for i in range(25)],
    'c': [101 + i*0.1 for i in range(25)],
    'v': [1000 + i*10 for i in range(25)]
}
SAMPLE_DATES = pd.to_datetime([f'2023-01-{i:02d}T00:00:00Z' for i in range(1, 26)])
SAMPLE_DF = pd.DataFrame(data=SAMPLE_BARS_DATA, index=SAMPLE_DATES)


@pytest.fixture
def runner():
    return CliRunner()

@patch('src.main.AlpacaService')
def test_backtest_cli_command_success(MockAlpacaService, runner):
    """Test the backtest CLI command runs successfully with mock data."""
    # Configure the mock AlpacaService
    mock_api_instance = MagicMock()
    mock_api_instance.get_bars.return_value.df = SAMPLE_DF

    mock_service_instance = MockAlpacaService.return_value
    mock_service_instance.api = mock_api_instance
    mock_service_instance.error_message = None

    # Run the CLI command
    result = runner.invoke(cli, [
        'backtest',
        '--start-date', '2023-01-01',
        '--end-date', '2023-01-05',
        '--symbol', 'AAPL'
    ])

    assert result.exit_code == 0
    assert "Backtest complete." in result.output
    assert "Final Portfolio Value" in result.output
    mock_api_instance.get_bars.assert_called_once_with(
        'AAPL', tradeapi.TimeFrame.Day, '2023-01-01', '2023-01-05'
    )

@patch('src.main.AlpacaService')
def test_backtest_cli_invalid_date_format(MockAlpacaService, runner):
    """Test CLI command with invalid date format."""
    result = runner.invoke(cli, [
        'backtest',
        '--start-date', '01-01-2023', # Invalid format
        '--end-date', '2023-01-05',
        '--symbol', 'AAPL'
    ])
    assert result.exit_code == 0 # Command itself doesn't exit with error, but prints error
    assert "Error: Invalid date format." in result.output

@patch('src.main.AlpacaService')
def test_backtest_cli_api_error_on_data_fetch(MockAlpacaService, runner):
    """Test CLI command when Alpaca API returns an error during data fetch."""
    mock_api_instance = MagicMock()
    mock_api_instance.get_bars.side_effect = Exception("API connection failed")

    mock_service_instance = MockAlpacaService.return_value
    mock_service_instance.api = mock_api_instance
    mock_service_instance.error_message = None

    result = runner.invoke(cli, [
        'backtest',
        '--start-date', '2023-01-01',
        '--end-date', '2023-01-05',
        '--symbol', 'FAKE'
    ])
    assert result.exit_code == 0
    assert "Error fetching or processing data for FAKE: API connection failed" in result.output

@patch('src.main.AlpacaService')
def test_backtest_cli_no_data_returned(MockAlpacaService, runner):
    """Test CLI command when no data is returned for the symbol/range."""
    mock_api_instance = MagicMock()
    mock_api_instance.get_bars.return_value.df = pd.DataFrame() # Empty DataFrame

    mock_service_instance = MockAlpacaService.return_value
    mock_service_instance.api = mock_api_instance
    mock_service_instance.error_message = None

    result = runner.invoke(cli, [
        'backtest',
        '--start-date', '2023-01-01',
        '--end-date', '2023-01-05',
        '--symbol', 'NODATA'
    ])
    assert result.exit_code == 0
    assert "No data found for NODATA in the given date range." in result.output


# Test for the SimpleSMAStrategy (more of an integration test with Backtrader)
def test_simple_sma_strategy_logic():
    """Test the SimpleSMAStrategy basic logic with mock data."""
    cerebro = bt.Cerebro()

    # Prepare data feed
    data_feed = bt.feeds.PandasData(dataname=SAMPLE_DF.copy()) # Use a copy
    cerebro.adddata(data_feed)

    # Add strategy
    cerebro.addstrategy(src.main.SimpleSMAStrategy, sma_period=3) # Use a small period for quick changes

    # Set initial cash
    cerebro.broker.setcash(100000.0)

    # Run the backtest
    results = cerebro.run()

    # Assertions (basic):
    # Check if the strategy ran and produced a result
    assert results is not None
    assert len(results) > 0 # Should have one strategy result

    # Check final portfolio value (can be more specific if expected outcome is known)
    final_value = cerebro.broker.getvalue()
    assert final_value != 100000.0 # Value should have changed if trades occurred

    # More detailed assertions could involve checking number of trades, positions, etc.
    # This requires knowing the exact behavior of the strategy with SAMPLE_DF.
    # For this simple strategy and data, it should make some trades.
    # Example: analyze trades if an analyzer was added
    # cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
    # analysis = results[0].analyzers.trade_analyzer.get_analysis()
    # assert analysis.total.total > 0 # Check if any trades were made

# Need to import tradeapi from alpaca_trade_api for the mock call assertion
import alpaca_trade_api as tradeapi
from alpaca_trade_api import TimeFrame # Import TimeFrame
# Also need to import SimpleSMAStrategy from src.main for the strategy test
import src.main
# Add a test for AlpacaService initialization failure
@patch('src.main.AlpacaService')
def test_backtest_cli_alpacaservice_init_fails(MockAlpacaService, runner):
    """Test CLI command when AlpacaService fails to initialize."""
    MockAlpacaService.return_value.api = None
    MockAlpacaService.return_value.error_message = "Failed to connect to Alpaca API"

    result = runner.invoke(cli, [
        'backtest',
        '--start-date', '2023-01-01',
        '--end-date', '2023-01-05',
        '--symbol', 'AAPL'
    ])

    assert result.exit_code == 0
    assert "Error: Failed to connect to Alpaca API" in result.output
    # Ensure get_bars was not called if service init failed early
    # This depends on how MockAlpacaService is set up. If api is None, it shouldn't be called.
    # mock_api_instance.get_bars.assert_not_called() # This would require mock_api_instance to be defined
    # A better check might be to see if the service's get_bars method was called.
    # For this, the mock needs to be on the method of the instance, or verify interaction with the instance.
    # However, the current structure of backtest() function creates a new AlpacaService instance.
    # So, the check is that the error message from the mocked service instance is printed.
    MockAlpacaService.assert_called_once() # Ensure the service was attempted to be initialized
    # Further checks could be added if the internal structure of backtest() was more complex
    # regarding AlpacaService usage after initialization.
    # For now, the output check is the primary validation.
