# Installation

## Requirements

- Python 3.10 or higher
- pip or uv package manager

## Basic Installation

Install biodbs using pip:

```bash
pip install biodbs
```

Or using uv:

```bash
uv add biodbs
```

## Optional Dependencies

biodbs has optional dependencies for additional features:

### Graph Module

For knowledge graph exports (NetworkX, RDF):

```bash
pip install biodbs[graph]
```

Or using uv:

```bash
uv add biodbs --optional graph
```

## Development Installation

For development, clone the repository and install in editable mode:

```bash
git clone https://github.com/qwerty239qwe/biodbs.git
cd biodbs
pip install -e ".[dev]"
```

Or using uv:

```bash
git clone https://github.com/qwerty239qwe/biodbs.git
cd biodbs
uv sync --all-extras
```

## Verifying Installation

Verify your installation by running:

```python
import biodbs
print(biodbs.__version__)

# Test a simple API call
from biodbs.fetch import uniprot_get_entry
entry = uniprot_get_entry("P04637")
print(entry.entries[0].protein_name)
```

## Dependencies

Core dependencies (installed automatically):

| Package | Purpose |
|---------|---------|
| `pandas` | DataFrame operations |
| `polars` | Alternative DataFrame library |
| `pydantic` | Data validation and models |
| `requests` | HTTP client for API calls |
| `scipy` | Statistical functions for ORA |

Optional dependencies (graph module):

| Package | Purpose |
|---------|---------|
| `networkx` | Graph algorithms and NetworkX export |
| `rdflib` | RDF/Turtle export |
