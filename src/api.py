from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field # For request/response models
from typing import List, Optional, Union

# Assuming AlpacaService is in src.main and can be imported
# Adjust import path if your structure is different or if main.py needs refactoring for AlpacaService
try:
    from src.main import AlpacaService
except ImportError:
    # This fallback might be needed if running api.py directly in a way that src. is not recognized
    # For robust solution, ensure PYTHONPATH is set correctly or refactor AlpacaService to a common module
    from main import AlpacaService


# Initialize FastAPI app
app = FastAPI(title="PyTrader API", version="1.0.0")

# Initialize AlpacaService
# This will load .env variables for API keys as defined in AlpacaService.__init__
alpaca_service = AlpacaService()

# Configure CORS
origins = [
    "http://localhost:5173",  # Default SvelteKit dev server
    "http://127.0.0.1:5173", # Also common for SvelteKit
    # Add other origins if needed, e.g., your production frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Pydantic Models for API requests and responses ---

class AccountInfoModel(BaseModel):
    account_number: str = Field(..., alias="Account Number")
    status: str = Field(..., alias="Status")
    equity: str = Field(..., alias="Equity")
    buying_power: str = Field(..., alias="Buying Power")
    cash: str = Field(..., alias="Cash")
    portfolio_value: str = Field(..., alias="Portfolio Value")
    daytrade_count: int = Field(..., alias="Daytrade Count")
    currency: str = Field(..., alias="Currency")

class PositionModel(BaseModel):
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: Optional[float] = None
    market_value: float
    unrealized_pl: float
    unrealized_plpc: float # Percentage
    asset_class: str
    exchange: str

class OrderRequestModel(BaseModel):
    symbol: str = Field(..., example="AAPL")
    qty: float = Field(..., example=10.5, description="Quantity to trade. For stocks, usually integer, but can be fractional for some assets/brokers.")
    side: str = Field(..., example="buy", pattern="^(buy|sell)$")
    order_type: str = Field(..., example="market", alias="type", pattern="^(market|limit|stop|stop_limit|trailing_stop)$")
    time_in_force: str = Field(..., example="day", pattern="^(day|gtc|opg|cls|ioc|fok)$")
    limit_price: Optional[float] = Field(None, example=150.00)
    stop_price: Optional[float] = Field(None, example=140.00)
    client_order_id: Optional[str] = Field(None, example="my_unique_order_id_123")

class OrderResponseModel(BaseModel):
    id: str
    client_order_id: Optional[str]
    symbol: str
    qty: float
    side: str
    type: str
    time_in_force: str
    status: str
    created_at: Optional[str]
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None

class ErrorDetail(BaseModel):
    error: str
    raw_error: Optional[str] = None

# --- API Endpoints ---

@app.on_event("startup")
async def startup_event():
    if alpaca_service.error_message and not alpaca_service.api:
        print(f"FastAPI Startup: AlpacaService initialization failed: {alpaca_service.error_message}")
        # Depending on severity, you might want to prevent startup or handle this.
        # For now, endpoints will return the error.
    elif not alpaca_service.api:
        print("FastAPI Startup: AlpacaService API not available for unknown reasons.")
    else:
        print("FastAPI Startup: AlpacaService initialized and API connected successfully.")


@app.get("/account", response_model=Union[AccountInfoModel, ErrorDetail], tags=["Account"])
async def get_account():
    """
    Retrieves detailed information about the trading account.
    """
    if alpaca_service.error_message and not alpaca_service.api:
        raise HTTPException(status_code=503, detail={"error": alpaca_service.error_message})
    if not alpaca_service.api:
        raise HTTPException(status_code=503, detail={"error": "Alpaca API not initialized."})

    account_info = alpaca_service.get_account_info()
    if "error" in account_info:
        raise HTTPException(status_code=500, detail=account_info)
    return account_info


@app.get("/positions", response_model=Union[List[PositionModel], ErrorDetail], tags=["Positions"])
async def get_positions():
    """
    Retrieves a list of current open positions.
    """
    if alpaca_service.error_message and not alpaca_service.api:
        raise HTTPException(status_code=503, detail={"error": alpaca_service.error_message})
    if not alpaca_service.api:
        raise HTTPException(status_code=503, detail={"error": "Alpaca API not initialized."})

    positions_data = alpaca_service.list_positions()
    if isinstance(positions_data, dict) and "error" in positions_data:
        raise HTTPException(status_code=500, detail=positions_data)
    return positions_data


@app.post("/orders", response_model=Union[OrderResponseModel, ErrorDetail], tags=["Trading"])
async def submit_order(order_data: OrderRequestModel):
    """
    Submits a new trade order.
    Ensure all required fields for the chosen order_type are provided.
    """
    if alpaca_service.error_message and not alpaca_service.api:
        raise HTTPException(status_code=503, detail={"error": alpaca_service.error_message})
    if not alpaca_service.api:
        raise HTTPException(status_code=503, detail={"error": "Alpaca API not initialized."})

    order_result = alpaca_service.submit_trade_order(
        symbol=order_data.symbol,
        qty=order_data.qty,
        side=order_data.side,
        order_type=order_data.order_type, # Use alias 'type' from Pydantic model
        time_in_force=order_data.time_in_force,
        limit_price=order_data.limit_price,
        stop_price=order_data.stop_price,
        client_order_id=order_data.client_order_id,
    )
    if "error" in order_result:
        # Check for specific Alpaca API error structure if available
        status_code = 400 # Bad Request by default for order submission issues
        if "raw_error" in order_result and "APIError(403" in order_result["raw_error"]: # Example: Forbidden
            status_code = 403
        elif "raw_error" in order_result and "APIError(422" in order_result["raw_error"]: # Example: Unprocessable Entity
            status_code = 422
        # Add more specific status codes based on common Alpaca errors if needed
        raise HTTPException(status_code=status_code, detail=order_result)
    return order_result

# --- Optional: Root endpoint for API health check or info ---
@app.get("/", tags=["General"])
async def read_root():
    return {"message": "Welcome to PyTrader API. Visit /docs for API documentation."}

# To run this FastAPI application (save as api.py in src directory):
# Ensure you are in the root directory of the project (PyTrader)
# Execute: uvicorn src.api:app --reload
# Then open your browser to http://127.0.0.1:8000/docs
#
# Note on imports:
# The `from src.main import AlpacaService` assumes that you run uvicorn from the project root.
# If `src` is not in PYTHONPATH or issues arise, you might need to adjust.
# One common way to handle this is to make `src` a package by ensuring `src/__init__.py` exists (it does),
# and then potentially refactoring `AlpacaService` into its own file if `main.py` becomes too large
# or has too many TUI-specifics that you don't want to load with the API.
# For now, this direct import should work if `uvicorn` is started from the project's root directory.

# Example of Pydantic model for Account for stricter typing (already defined above)
# class AccountInfo(BaseModel):
#     account_number: str
#     status: str
#     equity: str # Consider converting to float if calculations are needed on API side
#     buying_power: str
#     # ... add all fields from AlpacaService.get_account_info()

# Example of Pydantic model for Position (already defined above)
# class Position(BaseModel):
#     symbol: str
#     qty: str # Consider float
#     # ... add all fields from AlpacaService.list_positions()

# Example of Pydantic model for Order response (already defined above)
# class Order(BaseModel):
#     id: str
#     symbol: str
#     # ... add all fields from AlpacaService.submit_trade_order()

if __name__ == "__main__":
    import uvicorn
    # This is for direct execution of this file, e.g., python src/api.py
    # However, standard practice is `uvicorn src.api:app --reload` from the project root.
    print("Attempting to run uvicorn directly. Recommended: 'uvicorn src.api:app --reload' from project root.")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
