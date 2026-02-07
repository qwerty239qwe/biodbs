# Contributing

Thank you for your interest in contributing to biodbs!

## Getting Started

### Development Setup

1. Clone the repository:

```bash
git clone https://github.com/qwerty239qwe/biodbs.git
cd biodbs
```

2. Install dependencies with uv:

```bash
uv sync --all-extras
```

Or with pip:

```bash
pip install -e ".[dev]"
```

3. Run tests:

```bash
uv run pytest
```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_fetch/uniprot/

# Run with coverage
uv run pytest --cov=biodbs

# Run only fast tests (skip integration)
uv run pytest -m "not integration"
```

### Code Style

We use:

- **Black** for code formatting
- **isort** for import sorting
- **Ruff** for linting

```bash
# Format code
uv run black biodbs tests
uv run isort biodbs tests

# Lint
uv run ruff check biodbs
```

### Type Checking

```bash
uv run mypy biodbs
```

## Adding a New Database

### 1. Create the Fetcher

Create a new directory in `biodbs/fetch/`:

```
biodbs/fetch/newdb/
├── __init__.py
├── newdb_fetcher.py
└── funcs.py
```

### 2. Implement the Fetcher Class

```python
# biodbs/fetch/newdb/newdb_fetcher.py

from biodbs.fetch._base import BaseAPIConfig, BaseDataFetcher

class NewDB_APIConfig(BaseAPIConfig):
    HOST = "api.newdb.org"
    RATE_LIMIT = 10

    def __init__(self):
        super().__init__()
        self._base_url = "https://api.newdb.org"

class NewDB_Fetcher(BaseDataFetcher):
    def __init__(self):
        self._api_config = NewDB_APIConfig()
        super().__init__(self._api_config, ...)

    def get_entry(self, id: str):
        # Implementation
        pass
```

### 3. Create Data Models

Create Pydantic models in `biodbs/data/newdb/`:

```python
# biodbs/data/newdb/_data_model.py

from pydantic import BaseModel

class NewDBEntry(BaseModel):
    id: str
    name: str
    # ...
```

### 4. Add Convenience Functions

```python
# biodbs/fetch/newdb/funcs.py

from biodbs.fetch.newdb.newdb_fetcher import NewDB_Fetcher

def newdb_get_entry(id: str):
    fetcher = NewDB_Fetcher()
    return fetcher.get_entry(id)
```

### 5. Export Functions

Update `biodbs/fetch/__init__.py` and `biodbs/fetch/_func.py` to export the new functions.

### 6. Add Tests

Create tests in `tests/test_fetch/newdb/`:

```python
# tests/test_fetch/newdb/test_newdb_fetcher.py

import pytest
from biodbs.fetch.newdb import NewDB_Fetcher

class TestNewDBFetcher:
    def test_get_entry(self):
        fetcher = NewDB_Fetcher()
        result = fetcher.get_entry("TEST123")
        assert result is not None
```

### 7. Add Documentation

Create documentation in `docs/fetch/newdb.md`.

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-database`
3. Make your changes
4. Run tests: `uv run pytest`
5. Format code: `uv run black biodbs tests`
6. Commit with a clear message
7. Push and create a Pull Request

## Code Guidelines

- Use type hints for all function parameters and return values
- Write docstrings for all public functions
- Follow existing patterns in the codebase
- Keep functions focused and single-purpose
- Handle errors gracefully with informative messages

## Questions?

Open an issue on GitHub or start a discussion.
