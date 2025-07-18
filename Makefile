# Makefile

.PHONY: all clean venv install run

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

# Clean the project
clean:
	rm -rf .venv
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
