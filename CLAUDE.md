# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Dependencies
- `make setup` or `make install` - Create virtual environment and install all dependencies
- `make clean` - Remove virtual environment and cache files

### Code Quality
- `make lint` - Run ruff linter and formatter (auto-fixes issues)
- `make test` - Run pytest test suite

### Running the Application
- `make run` - Start the web application (equivalent to `uvicorn src.main:app --reload`)
- Access the application at `http://localhost:8000` after starting

### Single Test Execution
- `call .venv\Scripts\activate && pytest tests/test_main.py::test_specific_function` - Run specific test
- `call .venv\Scripts\activate && pytest tests/test_auth.py -v` - Run authentication tests with verbose output

## Architecture Overview

### Core Components

**FastAPI Web Application (src/main.py)**
- FastAPI-based web server with JWT authentication
- Serves static files (CSS, images) and Jinja2 templates
- Routes: `/` (login redirect), `/login`, `/token` (auth), `/home` (protected)
- Development server runs with auto-reload for rapid iteration

**Authentication System (src/auth/)**
- **security.py**: JWT token management, bcrypt password hashing, OAuth2 implementation
- **model.py**: Pydantic models for Token, TokenData, and UserInDB
- **routes.py**: Authentication route handlers (currently minimal)
- In-memory user database with test users: `johndoe`/`secret` (user), `jshull`/`password` (admin+user)

**Frontend Templates (src/templates/)**
- **auth/login.html**: Animated login form with floating label inputs
- **home.html**: Protected welcome page displaying authenticated user information
- Server-side rendered with Jinja2 templating engine

**Static Assets (src/static/)**
- **css/styles.css**: Professional styling with CSS custom properties for theming
- **img/**: SVG login icons and visual assets

### Configuration Files

**Environment Setup**
- Requires `.env` file for JWT secret key and other configuration
- `pyproject.toml` defines dependencies and tool configurations (ruff, pytest)

**Dependencies**
- Core web: `fastapi`, `uvicorn`, `jinja2`, `python-multipart`
- Authentication: `bcrypt`, `passlib`, `pyjwt`
- Configuration: `python-dotenv`
- Development: `pytest`
- Code quality: `ruff` (linting and formatting)

### Key Design Patterns

**JWT Authentication Flow**
- Login form submits credentials to `/token` endpoint
- Successful authentication returns JWT token stored in HTTP-only cookie
- Protected routes require valid JWT token for access
- Token contains user information and expiration timestamp

**Template-Based Rendering**
- Server-side HTML generation using Jinja2 templates
- Static CSS styling with custom properties for consistent theming
- Responsive design with animated form interactions

**Security Implementation**
- Password hashing with bcrypt for secure credential storage
- JWT tokens with configurable expiration times
- HTTP-only cookies to prevent XSS token theft
- OAuth2 password flow for standard authentication patterns

**Testing Architecture**
- FastAPI TestClient for endpoint testing
- Authentication flow testing with mock users
- Template rendering and static file serving tests

## Application Status

**Current State**: Early-stage web application with authentication foundation
- ✅ User authentication and session management
- ✅ Basic web infrastructure and routing
- ✅ Professional frontend styling and UX
- ⏳ Trading functionality (not yet implemented)
- ⏳ Stock quotes and market data integration
- ⏳ Portfolio management features
- ⏳ Order placement capabilities

**Future Development**: The `src/app/` directory is prepared for additional application modules and trading functionality.

## Important Notes

- The application currently focuses on authentication and web infrastructure
- Trading functionality from the original TUI version is not yet implemented
- Test users are available for development: `johndoe`/`secret` and `jshull`/`password`
- Windows-specific Makefile commands (uses `call` and `Scripts\activate`)