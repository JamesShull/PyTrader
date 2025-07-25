# Development Setup

Comprehensive guide for setting up PyTrader development environment.

## Development Dependencies

The project includes several development tools:

- **pytest** - Testing framework
- **playwright** - End-to-end testing
- **mkdocs** - Documentation generation
- **ruff** - Code linting and formatting (via Makefile)

## Project Structure

```
PyTrader/
├── src/                    # Source code
│   ├── auth/              # Authentication modules
│   │   ├── model.py       # Pydantic models
│   │   ├── routes.py      # Auth route handlers
│   │   └── security.py    # JWT and password handling
│   ├── static/            # Static assets
│   │   ├── css/           # Stylesheets
│   │   └── img/           # Images and icons
│   ├── templates/         # Jinja2 templates
│   │   ├── auth/          # Authentication templates
│   │   └── home.html      # Protected pages
│   └── main.py            # FastAPI application
├── tests/                 # Test files
├── docs/                  # MkDocs documentation
├── Makefile              # Development commands
└── pyproject.toml        # Project configuration
```

## Available Make Commands

### Setup and Installation
```bash
make install          # Create venv and install dependencies
make clean           # Remove venv and cache files
```

### Development
```bash
make run             # Start development server
make lint            # Run code linting and formatting
make test            # Run test suite
```

### Documentation
```bash
make docs-serve      # Serve documentation locally
make docs-build      # Build documentation
```

## Environment Variables

Create a `.env` file with:

```bash
SECRET_KEY=your-jwt-secret-key-here
```

## Code Style

The project uses:
- **Python 3.12+** - Modern Python features
- **Type hints** - For better code documentation
- **Async/await** - For FastAPI route handlers
- **Pydantic models** - For data validation

## Testing Strategy

### Unit Tests
- Authentication logic
- User management functions
- Token generation and validation

### Integration Tests
- FastAPI endpoint testing
- Template rendering
- Static file serving

### End-to-End Tests (Playwright)
- Login flow testing
- Page navigation
- Form interactions

## Git Workflow

1. Create feature branch
2. Make changes
3. Run tests: `make test`
4. Run linting: `make lint`
5. Commit changes
6. Submit pull request

## IDE Configuration

Recommended VS Code extensions:
- Python
- FastAPI
- Playwright Test for VS Code