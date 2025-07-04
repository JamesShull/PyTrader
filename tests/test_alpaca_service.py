import pytest
from respx import MockRouter
from dotenv import load_dotenv, find_dotenv
import os
import time
from unittest.mock import patch

from ratelimit import RateLimitException

# Load .env file before importing AlpacaService.
# This helps if you have a .env file for local testing with real (paper) keys,
# but tests should primarily rely on mocked environments.
# For CI, environment variables should be set directly or via CI secrets.
load_dotenv(find_dotenv(), override=True) # override=True allows env vars to take precedence

# Now import the service
from src.main import AlpacaService # noqa: E402 module level import not at top of file

MOCK_PAPER_URL = "https://paper-api.alpaca.markets" # Default mock URL
MOCK_TEST_KEY_ID = "test_fixture_key_id"
MOCK_TEST_SECRET_KEY = "test_fixture_secret_key"

@pytest.fixture
def manage_env_vars_for_service(monkeypatch):
    """
    Manages Alpaca environment variables for service tests.
    Uses monkeypatch to set default testing env vars if not already set.
    This ensures tests run consistently with mockable values.
    """
    # Unset existing Alpaca environment variables to ensure a clean state for monkeypatch
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)

    # Now set the desired mock values
    monkeypatch.setenv("APCA_API_KEY_ID", MOCK_TEST_KEY_ID)
    monkeypatch.setenv("APCA_API_SECRET_KEY", MOCK_TEST_SECRET_KEY)
    monkeypatch.setenv("APCA_API_BASE_URL", MOCK_PAPER_URL)

    yield # Test runs here

    # monkeypatch will automatically restore the original state (or un-set if they were not set before)


@pytest.fixture
def alpaca_service_valid_keys(monkeypatch, respx_mock: MockRouter):
    """
    Fixture for AlpacaService with valid keys and mocked initial connection.
    It sets specific mock environment variables for its scope.
    """
    monkeypatch.setenv("APCA_API_KEY_ID", "valid_mock_key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "valid_mock_secret")
    monkeypatch.setenv("APCA_API_BASE_URL", MOCK_PAPER_URL)

    # Mock the initial get_account call made during AlpacaService.__init__
    route = respx_mock.get(f"{MOCK_PAPER_URL}/v2/account").respond(json={"status": "ACTIVE", "account_number": "mock_fixture_account"})

    respx_mock.start() # Explicitly start the router
    service = AlpacaService()
    respx_mock.stop() # Stop router after instantiation

    assert route.called, f"Initial /v2/account mock was not called for {MOCK_PAPER_URL}"
    assert service.api is not None, "API should be initialized successfully in alpaca_service_valid_keys"
    assert service.error_message is None, "No error message should be present on successful init in alpaca_service_valid_keys"
    return service

@pytest.fixture
def alpaca_service_no_keys(monkeypatch): # Removed respx_mock as it's not used when keys are missing
    """
    Fixture to provide an AlpacaService instance with intentionally missing keys.
    It uses monkeypatch to ensure keys are removed only for this test's scope.
    """
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)
    # Set a base URL because AlpacaService will try to use it.
    # The connection should fail due to no keys, not due to a bad URL.
    # Or, more accurately, it should fail before even trying to connect.
    monkeypatch.setenv("APCA_API_BASE_URL", MOCK_PAPER_URL)
    # No need to mock http call here as it should fail before that due to missing keys.
    # AlpacaService's __init__ checks for keys first.

    service = AlpacaService()
    return service

def test_alpaca_service_init_no_keys(alpaca_service_no_keys: AlpacaService):
    """Test AlpacaService initialization with missing API keys."""
    service = alpaca_service_no_keys
    assert service.api is None
    assert service.error_message is not None
    assert "API keys not found" in service.error_message

@pytest.mark.usefixtures("manage_env_vars_for_service") # Ensures env vars are set and cleaned up
def test_get_account_info_success(respx_mock: MockRouter, alpaca_service_valid_keys: AlpacaService):
    """Test successful retrieval of account information."""
    # alpaca_service_valid_keys fixture already handles initial connection mock
    service = alpaca_service_valid_keys
    assert service.api is not None
    assert service.error_message is None

    mock_account_data = {
        "account_number": "123456789",
        "status": "ACTIVE",
        "equity": "100000.00",
        "buying_power": "200000.00",
        "cash": "50000.00",
        "portfolio_value": "100000.00",
        "daytrade_count": 0,
        "currency": "USD"
    }
    # Mock the /v2/account endpoint
    respx_mock.get("/v2/account").respond(json=mock_account_data)

    # This call is to test the connection during AlpacaService initialization
    # It should have been made when alpaca_service_valid_keys was created.
    # We need to ensure this fixture setup correctly mocks the initial get_account call too.
    # For this specific test, we are testing the get_account_info method call.

    account_info = service.get_account_info()

    assert "error" not in account_info
    assert account_info["Account Number"] == "123456789"
    assert account_info["Equity"] == "$100,000.00"
    assert respx_mock.get("/v2/account").called


@pytest.mark.respx(base_url="https://paper-api.alpaca.markets")
def test_get_account_info_api_error(respx_mock: MockRouter, alpaca_service_valid_keys: AlpacaService):
    """Test handling of API error when retrieving account information."""
    service = alpaca_service_valid_keys
    assert service.api is not None

    respx_mock.get("/v2/account").respond(status_code=500, json={"message": "Internal Server Error"})

    account_info = service.get_account_info()

    assert "error" in account_info
    assert "Failed to fetch account info" in account_info["error"]
    assert "500" in account_info["error"] # Check if status code or error message is propagated


def test_alpaca_service_init_connection_failure(respx_mock: MockRouter, monkeypatch): # Added monkeypatch
    """Test AlpacaService initialization when the initial connection fails."""
    # This test needs to control the environment variables before AlpacaService is instantiated
    # os.environ["APCA_API_KEY_ID"] = "conn_fail_key" # Replaced by monkeypatch
    # os.environ["APCA_API_SECRET_KEY"] = "conn_fail_secret" # Replaced by monkeypatch
    # base_url = "https://paper-api.alpaca.markets" # Not used
    monkeypatch.setenv("APCA_API_KEY_ID", "conn_fail_key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "conn_fail_secret")
    # Using a localhost URL that's unlikely to be in use, to simulate a connection failure
    # if respx doesn't intercept, or to be properly intercepted by respx.
    failure_url = "http://localhost:65533"
    monkeypatch.setenv("APCA_API_BASE_URL", failure_url)

    # Mock the get_account call for this specific URL to return a 503 status
    route = respx_mock.get(f"{failure_url}/v2/account").respond(status_code=503)

    respx_mock.start()
    service = AlpacaService()
    respx_mock.stop()

    assert route.called, f"Initial /v2/account mock was not called for {failure_url}"
    assert service.api is None
    assert service.error_message is not None
    # The error message from alpaca-trade-api for a 503 might be specific
    assert f"Failed to connect to Alpaca API at {failure_url}" in service.error_message
    # Check for the specific part of the error that indicates an APIError or similar
    # For example, the SDK might raise APIError which includes the status code in its string representation.
    # Or it might be a generic connection error message from the underlying HTTP library if the mock isn't perfect.
    # Given the previous "Name or service not known", respx might not have been catching it.
    # If respx *does* catch it now with localhost, the error should reflect the 503.
    assert "APIError" in service.error_message or "503" in service.error_message or "service unavailable" in service.error_message.lower()

    # No explicit cleanup of env vars needed due to monkeypatch


# It's good practice to ensure that tests clean up environment variables they set,
# especially if they could affect other tests. Fixtures are better for this.

@pytest.fixture(autouse=True)
def manage_env_vars():
    """Fixture to save and restore critical Alpaca environment variables."""
    original_vars = {
        "APCA_API_KEY_ID": os.environ.get("APCA_API_KEY_ID"),
        "APCA_API_SECRET_KEY": os.environ.get("APCA_API_SECRET_KEY"),
        "APCA_API_BASE_URL": os.environ.get("APCA_API_BASE_URL"),
    }
    yield
    # Restore original environment variables
    for key, value in original_vars.items():
        if value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = value

# --- Tests for get_quotes ---

@pytest.mark.usefixtures("manage_env_vars_for_service")
def test_get_quotes_success(respx_mock: MockRouter, alpaca_service_valid_keys: AlpacaService):
    """Test successful retrieval of quotes for multiple symbols."""
    service = alpaca_service_valid_keys
    assert service.api is not None # Ensured by fixture

    symbols = ["AAPL", "MSFT"]
    mock_quotes_response = {
        "AAPL": {"ap": 150.12, "bp": 150.10, "as": 10, "bs": 12, "t": "2023-10-26T10:00:00Z"},
        "MSFT": {"ap": 330.50, "bp": 330.45, "as": 8, "bs": 15, "t": "2023-10-26T10:00:00Z"},
    }
    # Ensure the URL matches how Alpaca SDK constructs it for get_latest_quotes
    # It will be /v2/stocks/quotes/latest?symbols=AAPL,MSFT (or similar, check SDK docs if specific)
    # For simplicity, let's assume a general quotes endpoint if the exact one is complex.
    # The tradeapi.REST.get_latest_quotes uses /v2/stocks/quotes/latest
    respx_mock.get(f"{MOCK_PAPER_URL}/v2/stocks/quotes/latest", params={"symbols": ",".join(symbols)}).respond(json={"quotes": mock_quotes_response})

    quotes = service.get_quotes(symbols)

    assert "error" not in quotes
    assert "AAPL" in quotes
    assert quotes["AAPL"]["ask_price"] == 150.12
    assert quotes["MSFT"]["bid_price"] == 330.45
    assert respx_mock.calls.call_count == 1 # After the initial get_account in fixture

@pytest.mark.usefixtures("manage_env_vars_for_service")
def test_get_quotes_api_error(respx_mock: MockRouter, alpaca_service_valid_keys: AlpacaService):
    """Test API error during quote retrieval."""
    service = alpaca_service_valid_keys
    symbols = ["FAIL1"]

    respx_mock.get(f"{MOCK_PAPER_URL}/v2/stocks/quotes/latest", params={"symbols": ",".join(symbols)}).respond(status_code=500, json={"message": "Internal Server Error"})

    quotes = service.get_quotes(symbols)

    assert "error" in quotes
    assert "Failed to fetch quotes" in quotes["error"]
    assert "500" in quotes["error"]

@pytest.mark.usefixtures("manage_env_vars_for_service")
def test_get_quotes_empty_symbols_list(alpaca_service_valid_keys: AlpacaService):
    """Test get_quotes with an empty list of symbols."""
    service = alpaca_service_valid_keys
    quotes = service.get_quotes([])
    assert quotes == {} # Expect an empty dictionary

@pytest.mark.usefixtures("manage_env_vars_for_service")
def test_get_quotes_partial_success_or_symbol_not_found(respx_mock: MockRouter, alpaca_service_valid_keys: AlpacaService):
    """Test how get_quotes handles responses where some symbols might not be found or have issues."""
    service = alpaca_service_valid_keys
    symbols = ["GOOD", "BAD"] # Assume BAD might not be returned or is invalid

    # Mock response only contains data for "GOOD"
    mock_partial_response = {
        "GOOD": {"ap": 100.00, "bp": 99.90, "as": 5, "bs": 7, "t": "2023-10-26T11:00:00Z"}
    }
    respx_mock.get(f"{MOCK_PAPER_URL}/v2/stocks/quotes/latest", params={"symbols": ",".join(symbols)}).respond(json={"quotes": mock_partial_response})

    quotes = service.get_quotes(symbols)

    assert "error" not in quotes
    assert "GOOD" in quotes
    assert quotes["GOOD"]["ask_price"] == 100.00
    assert "BAD" not in quotes # SDK might filter out symbols not in response, or handle differently.
                               # This test assumes keys not in response are omitted.

def test_get_quotes_service_not_initialized(alpaca_service_no_keys: AlpacaService):
    """Test get_quotes when AlpacaService failed to initialize (e.g., no API keys)."""
    service = alpaca_service_no_keys # This fixture provides a service with .api = None and error_message set
    quotes = service.get_quotes(["AAPL"])
    assert "error" in quotes
    assert "API keys not found" in quotes["error"] # Or whatever error_message is set to by alpaca_service_no_keys

# Example of mocking the Alpaca API's quote object structure if needed for more detailed tests
# from alpaca_trade_api.entity import Quote as AlpacaQuote
# from alpaca_trade_api.common import APIError
# This would be if you were testing the internal processing of the Quote objects more deeply.
# For these tests, mocking the JSON response is generally sufficient.

# --- Tests for Rate Limiting ---

MOCK_ACCOUNT_DATA_FOR_RATE_LIMIT_TESTS = {
    "account_number": "rate_limit_test_acct",
    "status": "ACTIVE",
    "equity": "1000.00",
    "buying_power": "2000.00",
    "cash": "500.00",
    "portfolio_value": "1000.00",
    "daytrade_count": 0,
    "currency": "USD"
}

MOCK_QUOTES_DATA_FOR_RATE_LIMIT_TESTS = {
    "XYZ": {"ap": 10.10, "bp": 10.00, "as": 10, "bs": 10, "t": "2023-10-27T10:00:00Z"}
}

@pytest.mark.usefixtures("manage_env_vars_for_service")
@patch('time.sleep', return_value=None) # Mock time.sleep to prevent actual delays
def test_get_account_info_rate_limit_per_second(
    mock_sleep, respx_mock: MockRouter, alpaca_service_valid_keys: AlpacaService
):
    """Test per-second rate limit for get_account_info."""
    service = alpaca_service_valid_keys
    respx_mock.get("/v2/account").respond(json=MOCK_ACCOUNT_DATA_FOR_RATE_LIMIT_TESTS)

    # Exhaust the per-second limit (10 calls)
    for i in range(10):
        print(f"Call {i+1} within per-second limit")
        account_info = service.get_account_info()
        assert "error" not in account_info, f"Call {i+1} failed unexpectedly"
        assert respx_mock.get("/v2/account").call_count == i + 1


    # Next call should trigger rate limit
    print("Call 11, expecting rate limit")
    account_info_ratelimited = service.get_account_info()
    assert "error" in account_info_ratelimited
    assert "Rate limit exceeded" in account_info_ratelimited["error"]
    # The actual API call should not happen if rate limit is correctly applied before the call
    assert respx_mock.get("/v2/account").call_count == 10 # Should not have increased

    # Wait for the rate limit period to pass (mocked)
    # time.sleep(1) # Original call to time.sleep
    # In the ratelimit library, the period is 1 second.
    # To reset the limit, we need to advance time.
    # However, the decorator itself raises RateLimitException immediately.
    # The library's internal clock needs to be considered.
    # For testing, we rely on the exception being raised.
    # If we wanted to test *after* the period, we'd need to manipulate the library's clock
    # or use a more sophisticated time mocking like `freezegun`.
    # For now, verifying the exception is sufficient.

@pytest.mark.usefixtures("manage_env_vars_for_service")
@patch('time.sleep', return_value=None) # Mock time.sleep
def test_get_quotes_rate_limit_per_second(
    mock_sleep, respx_mock: MockRouter, alpaca_service_valid_keys: AlpacaService
):
    """Test per-second rate limit for get_quotes."""
    service = alpaca_service_valid_keys
    symbols = ["XYZ"]
    respx_mock.get(f"{MOCK_PAPER_URL}/v2/stocks/quotes/latest", params={"symbols": ",".join(symbols)}).respond(json={"quotes": MOCK_QUOTES_DATA_FOR_RATE_LIMIT_TESTS})

    for i in range(10):
        quotes = service.get_quotes(symbols)
        assert "error" not in quotes
        assert respx_mock.calls.call_count == i + 1 # Each call hits the mock

    quotes_ratelimited = service.get_quotes(symbols)
    assert "error" in quotes_ratelimited
    assert "Rate limit exceeded" in quotes_ratelimited["error"]
    assert respx_mock.calls.call_count == 10


# Note: Testing the per-minute limit (200 calls) directly would be slow even with mocked sleep,
# as it would involve 200 loop iterations.
# The logic for per-minute and per-second limits is the same in the `ratelimit` library.
# Thus, testing the per-second limit thoroughly gives good confidence.
# If specific interaction between the two limits needed testing, a more complex setup
# with time manipulation (e.g., using `freezegun`) would be beneficial.

@pytest.mark.usefixtures("manage_env_vars_for_service")
@patch('time.time') # Mock time.time for finer control if needed by ratelimit internals
@patch('time.sleep', return_value=None)
def test_get_account_info_rate_limit_per_minute_conceptual(
    mock_sleep, mock_time, respx_mock: MockRouter, alpaca_service_valid_keys: AlpacaService
):
    """
    Conceptual test for per-minute rate limit for get_account_info.
    This test illustrates the idea but won't run 200 iterations for speed.
    It relies on the `ratelimit` library correctly handling multiple decorators.
    """
    service = alpaca_service_valid_keys
    # Assume current time is 0 for simplicity in this conceptual test
    mock_time.return_value = 0.0

    # Mock the API response
    respx_mock.get("/v2/account").respond(json=MOCK_ACCOUNT_DATA_FOR_RATE_LIMIT_TESTS)

    # Simulate making 10 calls (well within 200/min, but hits 10/sec)
    for i in range(10):
        # print(f"Minute test call {i+1}")
        account_info = service.get_account_info()
        assert "error" not in account_info, f"Call {i+1} (minute test) failed"

    # This call should be rate-limited by the 10 calls/sec limit
    # print("Minute test call 11 (expecting per-second limit)")
    account_info_ratelimited_sec = service.get_account_info()
    assert "error" in account_info_ratelimited_sec
    assert "Rate limit exceeded" in account_info_ratelimited_sec["error"]
    # Total calls to actual API should be 10
    assert respx_mock.get("/v2/account").call_count == 10

    # Now, let's advance time by 1 second to bypass the per-second limit,
    # but still be within the same minute for the per-minute limit.
    mock_time.return_value = 1.0
    # The ratelimit library stores the time of the last call.
    # Advancing time with mock_time should allow subsequent calls if the period has passed.

    # The following calls would test the 200/min limit if we made enough.
    # For this conceptual test, we'll just make one more call.
    # This call should now pass the per-second limit because time has advanced.
    # print("Minute test call 12 (expecting success after 1s wait)")
    account_info_after_wait = service.get_account_info()
    assert "error" not in account_info_after_wait, \
        f"Call after 1s wait failed: {account_info_after_wait.get('error', '')}"
    assert respx_mock.get("/v2/account").call_count == 11 # One more successful call

    # To truly test the 200/min limit, one would need to:
    # 1. Make 10 calls.
    # 2. Advance time by 1s.
    # 3. Make another 10 calls.
    # 4. Repeat until 200 calls are made within less than 60s of mocked time.
    # 5. The 201st call (if made before 60s of mocked time have passed from the first call)
    #    should then be blocked by the per-minute limit.
    # This is complex with basic time mocking. `freezegun` is better suited for this.
    # Given the library's reliability, testing the stricter per-second limit and
    # ensuring the decorators are applied is usually sufficient.
    pass # Test is conceptual and focuses on the interaction
