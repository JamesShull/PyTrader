# Installation

This guide will help you set up PyTrader on your local development environment.

## Prerequisites

- Python 3.12 or higher
- Git
- UV package manager (recommended) or pip

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd PyTrader
```

### 2. Create Virtual Environment and Install Dependencies

Using the provided Makefile:

```bash
make install
```

This command will:
- Create a virtual environment using `uv venv`
- Install all dependencies including development tools

### 3. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.sample .env
```

Configure the following variables:
- `SECRET_KEY` - JWT secret key for token signing

### 4. Verify Installation

Run the test suite to verify everything is working:

```bash
make test
```

## Alternative Installation Methods

### Using pip directly

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .[dev]
```

## Next Steps

Continue to the [Quick Start](quickstart.md) guide to run the application.