# Makefile

.PHONY: all clean venv install run lint test docs-serve docs-build

all: install

# Create a virtual environment
venv:
	uv venv

# Install dependencies
install: venv
	. .venv/bin/activate; uv pip install -e .[dev]

# Run the application
run:
	. .venv/bin/activate; uvicorn src.main:app --reload

# Run tests
test:
	. .venv/bin/activate; pytest

# Run linting and formatting
lint:
	. .venv/bin/activate; ruff check --fix .; ruff format .

# Serve documentation locally
docs-serve:
	. .venv/bin/activate; mkdocs serve

# Build documentation
docs-build:
	. .venv/bin/activate; mkdocs build

# Clean the project
clean:
	rm -rf .venv
	rm -rf site
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
