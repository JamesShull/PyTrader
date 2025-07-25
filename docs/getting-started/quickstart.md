# Quick Start

Get PyTrader up and running in minutes.

## Running the Application

### Start the Development Server

```bash
make run
```

Or manually:

```bash
source .venv/bin/activate
uvicorn src.main:app --reload
```

The application will be available at `http://localhost:8000`

## Default User Credentials

The application comes with a test user for development:

- **Username:** `admin`
- **Password:** `admin`
- **Scope:** `admin`

## Application Routes

- `/` - Redirects to login page
- `/login` - User authentication form
- `/token` - Authentication endpoint (POST)
- `/home` - Protected welcome page (requires authentication)

## Testing the Application

### Run All Tests

```bash
make test
```

### Run Specific Tests

```bash
# Run authentication tests
source .venv/bin/activate
pytest tests/ -v

# Run Playwright tests
pytest tests/test_playwright.py -v
```

## Development Workflow

1. **Start the server:** `make run`
2. **Make changes** to source code
3. **Server auto-reloads** with changes
4. **Run tests:** `make test`
5. **Check code quality:** `make lint`

## Next Steps

- Explore the [API Documentation](../api/authentication.md)
- Learn about [Development Setup](../development/setup.md)
- Review the authentication system implementation