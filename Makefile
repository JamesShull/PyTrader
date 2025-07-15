# Makefile for Alpaca TUI Trader

.PHONY: help setup install clean run lint

help:
	@echo "Commands:"
	@echo "  setup        : Create virtual environment and install dependencies"
	@echo "  install      : Install dependencies"
	@echo "  clean        : Remove virtual environment and cache files"
	@echo "  run          : Run the TUI application"
	@echo "  lint         : Run ruff linter and formatter"

# Variables
PYTHON = python3
VENV_DIR = .venv
REQS_FILE = requirements.txt

# Default target: Create venv, generate requirements, install deps
all: setup

# Ensure venv exists and uv is installed
$(VENV_DIR)/bin/activate:
	test -d $(VENV_DIR) || $(PYTHON) -m venv $(VENV_DIR)
	@echo "Ensuring uv is installed in the virtual environment..."
	. $(VENV_DIR)/bin/activate && pip install --upgrade pip uv > /dev/null
	touch $(VENV_DIR)/bin/activate # Update timestamp

# Generate requirements.txt from pyproject.toml
# This target depends on the venv being ready with uv.
$(REQS_FILE): pyproject.toml $(VENV_DIR)/bin/activate
	@echo "Generating $(REQS_FILE) from pyproject.toml..."
	. $(VENV_DIR)/bin/activate && uv pip compile pyproject.toml -o $(REQS_FILE)

# Setup: Alias for installing dependencies, implicitly handles venv and reqs generation
setup: install

# Install dependencies from requirements.txt and dev dependencies from pyproject.toml
# This target depends on requirements.txt being up-to-date.
install: $(REQS_FILE)
	@echo "Installing dependencies from $(REQS_FILE) and dev dependencies..."
	. $(VENV_DIR)/bin/activate && uv pip install -r $(REQS_FILE)
	. $(VENV_DIR)/bin/activate && uv pip install -e .[test]
	@echo "Dependencies installed. To activate the virtual environment, run: source $(VENV_DIR)/bin/activate"

# Clean up virtual environment and cache files
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_DIR)
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	rm -f $(REQS_FILE)

# Run the TUI application
run: $(VENV_DIR)/bin/activate src/main.py
	@echo "Starting Alpaca TUI Trader..."
	. $(VENV_DIR)/bin/activate && $(PYTHON) src/main.py run_tui

# Run ruff linter and formatter
lint: $(VENV_DIR)/bin/activate
	@echo "Running ruff linter and formatter..."
	. $(VENV_DIR)/bin/activate && ruff check . --fix && ruff format . && ruff check .

# Run tests
test: $(VENV_DIR)/bin/activate
	@echo "Running tests..."
	. $(VENV_DIR)/bin/activate && export PYTHONPATH=./src && pytest

# Create src directory and main.py if they don't exist
# This also ensures __init__.py is present for hatch versioning
src/main.py:
	mkdir -p src
	touch src/main.py
	touch src/__init__.py # Ensure it exists, content is in pyproject.toml implicitly

# Ensure src/__init__.py has version for hatch, if not using hatch build directly
# This is more of a note, actual version management is via pyproject.toml and hatch/uv
src/__init__.py:
	mkdir -p src
	touch src/__init__.py
	# If src/__init__.py is empty and you need to populate version for some tools:
	# if ! grep -q "__version__" src/__init__.py; then echo '__version__ = "0.1.0"' > src/__init__.py; fi
