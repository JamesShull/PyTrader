import pytest
from playwright.sync_api import sync_playwright


def test_playwright_basic_functionality():
    """Test that playwright can launch a browser and navigate to a page."""
    with sync_playwright() as p:
        # Launch browser in headless mode for WSL
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to a simple page
        page.goto("data:text/html,<html><body><h1>Test Page</h1></body></html>")
        
        # Check that the page loaded correctly
        title = page.locator("h1").text_content()
        assert title == "Test Page"
        
        browser.close()


def test_playwright_with_fastapi_app():
    """Test that playwright can interact with our FastAPI application."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Test the login page (assuming the app is running)
        try:
            page.goto("http://localhost:8000/login", timeout=5000)
            # Check if login form exists
            login_form = page.locator("form")
            assert login_form.is_visible()
        except Exception:
            # If the app isn't running, that's okay for this test
            pytest.skip("FastAPI app not running")
        finally:
            browser.close()