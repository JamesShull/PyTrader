import pytest
from respx import MockRouter
from dotenv import load_dotenv, find_dotenv
import os

# Load .env file before importing AlpacaService, especially if .env is in root
# and tests are run from root.
# Ensure this runs before 'src.main' is imported if 'src.main' initializes AlpacaService at module level.
if find_dotenv():
    load_dotenv(find_dotenv(), override=True)
else:
    # Fallback for CI or environments where .env might not be present
    # Set minimal required env vars for tests to run without real keys
    os.environ.setdefault("APCA_API_KEY_ID", "test_key_id")
    os.environ.setdefault("APCA_API_SECRET_KEY", "test_secret_key")
    os.environ.setdefault("APCA_API_BASE_URL", "http://localhost:12345") # Mocked URL

# Now import the service
from src.main import AlpacaService # noqa: E402 module level import not at top of file

MOCK_PAPER_URL = "https://paper-api.alpaca.markets"

@pytest.fixture
def manage_env_vars_for_service():
    """Saves and restores Alpaca env vars, setting testing defaults if not present."""
    original_vars = {
        "APCA_API_KEY_ID": os.environ.get("APCA_API_KEY_ID"),
        "APCA_API_SECRET_KEY": os.environ.get("APCA_API_SECRET_KEY"),
        "APCA_API_BASE_URL": os.environ.get("APCA_API_BASE_URL"),
    }
    # Set defaults for tests if not overridden by a specific test case
    os.environ.setdefault("APCA_API_KEY_ID", "default_test_key")
    os.environ.setdefault("APCA_API_SECRET_KEY", "default_test_secret")
    os.environ.setdefault("APCA_API_BASE_URL", MOCK_PAPER_URL)
    yield
    for key, value in original_vars.items():
        if value is None:
            if key in os.environ: del os.environ[key]
        else:
            os.environ[key] = value

@pytest.fixture
def alpaca_service_valid_keys(manage_env_vars_for_service, respx_mock: MockRouter):
    """
    Fixture for AlpacaService with valid keys and mocked initial connection.
    Ensures the AlpacaService.__init__ call to get_account is mocked.
    """
    os.environ["APCA_API_KEY_ID"] = "test_key_id_valid"
    os.environ["APCA_API_SECRET_KEY"] = "test_secret_key_valid"
    os.environ["APCA_API_BASE_URL"] = MOCK_PAPER_URL

    # Mock the initial get_account call made during AlpacaService.__init__
    respx_mock.get(f"{MOCK_PAPER_URL}/v2/account").respond(json={"status": "ACTIVE"})

    service = AlpacaService()
    # Important: after service init, clear mocks if sub-tests want to set their own for same URL
    # However, for this fixture, the initial call is the primary concern.
    # Tests using this fixture will add their own mocks for subsequent calls.
    return service

@pytest.fixture
def alpaca_service_no_keys(manage_env_vars_for_service):
    """Fixture to provide an AlpacaService instance with intentionally missing keys."""
    original_key = os.environ.pop("APCA_API_KEY_ID", None)
    original_secret = os.environ.pop("APCA_API_SECRET_KEY", None)
    service = AlpacaService()
    # Restore original keys if they existed
    if original_key:
        os.environ["APCA_API_KEY_ID"] = original_key
    if original_secret:
        os.environ["APCA_API_SECRET_KEY"] = original_secret
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


def test_alpaca_service_init_connection_failure(respx_mock: MockRouter):
    """Test AlpacaService initialization when the initial connection fails."""
    # This test needs to control the environment variables before AlpacaService is instantiated
    os.environ["APCA_API_KEY_ID"] = "conn_fail_key"
    os.environ["APCA_API_SECRET_KEY"] = "conn_fail_secret"
    base_url = "https://paper-api.alpaca.markets"
    os.environ["APCA_API_BASE_URL"] = base_url

    respx_mock.get(f"{base_url}/v2/account").respond(status_code=503) # Service Unavailable

    service = AlpacaService() # Initialization happens here and makes a get_account call

    assert service.api is None
    assert service.error_message is not None
    assert "Failed to connect to Alpaca API" in service.error_message
    assert "503" in service.error_message

    # Clean up env vars if necessary, or ensure fixtures handle this
    del os.environ["APCA_API_KEY_ID"]
    del os.environ["APCA_API_SECRET_KEY"]
    del os.environ["APCA_API_BASE_URL"]

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
