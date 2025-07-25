# Testing Guide

Comprehensive testing documentation for PyTrader.

## Testing Framework

PyTrader uses **pytest** as the primary testing framework with additional tools:

- **pytest** - Core testing framework
- **Playwright** - End-to-end browser testing
- **FastAPI TestClient** - API endpoint testing

## Test Structure

```
tests/
├── test_playwright.py     # Browser-based tests
└── [future test files]    # Additional test modules
```

## Running Tests

### All Tests
```bash
make test
```

### Specific Test Files
```bash
# Activate virtual environment first
source .venv/bin/activate

# Run specific test file
pytest tests/test_playwright.py -v

# Run specific test function
pytest tests/test_playwright.py::test_playwright_basic_functionality -v
```

## Playwright Testing

### Browser Configuration

Tests run in **headless mode** for WSL compatibility:

```python
browser = p.chromium.launch(headless=True)
```

### Example Test Structure

```python
def test_playwright_basic_functionality():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Test actions
        page.goto("http://localhost:8000/login")
        
        # Assertions
        assert page.locator("form").is_visible()
        
        browser.close()
```

### Available Browsers
- **Chromium** - Primary browser for testing
- **Firefox** - Available if needed
- **WebKit** - Safari engine testing

## Test Categories

### Unit Tests (Planned)
- Authentication functions
- User validation
- Token generation
- Password hashing

### Integration Tests (Planned)
- FastAPI endpoint testing
- Database operations
- Template rendering

### End-to-End Tests (Current)
- Login flow
- Page navigation
- Form interactions
- Browser compatibility

## Test Data

### Test User
- **Username:** `admin`
- **Password:** `admin`
- **Scope:** `admin`

### Test URLs
- **Login:** `http://localhost:8000/login`
- **Home:** `http://localhost:8000/home`
- **Token:** `http://localhost:8000/token`

## Best Practices

### Test Isolation
- Each test should be independent
- Clean up resources (close browsers)
- Use test-specific data

### Assertions
- Use descriptive assertion messages
- Test both positive and negative cases
- Verify expected behavior thoroughly

### Performance
- Keep tests fast and focused
- Use headless mode for CI/CD
- Avoid unnecessary waiting

## Continuous Integration

Tests are designed to run in CI environments:
- Headless browser mode
- No GUI dependencies
- Fast execution times

## Debugging Tests

### Verbose Output
```bash
pytest tests/ -v -s
```

### Debug Mode
```python
# Add for debugging
browser = p.chromium.launch(headless=False, slow_mo=1000)
```

### Screenshots
```python
# Capture screenshots on failure
page.screenshot(path="debug.png")
```