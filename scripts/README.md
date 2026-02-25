# CLI Support Scripts

This directory contains scripts for managing the CLI tool.

## Generate API Client

The `generate_client.sh` script generates the API client from the OpenAPI specification using `datamodel-code-generator` (Pydantic v2).

### Usage

```bash
# Generate from local openapi.json
./scripts/generate_client.sh --input openapi.json

# Generate from remote server
./scripts/generate_client.sh --input http://192.168.1.100/api/v1/openapi.json

# Specify custom output directory
./scripts/generate_client.sh --input openapi.json --output th_cli/api_lib_autogen
```

### Features

- ✅ **Pure Python** - No Docker required
- ✅ **Fast** - 10-20x faster than old openapi-generator
- ✅ **Pydantic v2** - 5-50x faster validation
- ✅ **Type-safe** - Full type hints and IDE support
- ✅ **Modern** - Uses latest async patterns

### Generated Structure

```
th_cli/api_lib_autogen/
├── __init__.py          # Package exports
├── models.py            # Pydantic v2 models
├── api_client.py        # HTTP client with middleware
├── exceptions.py        # Custom exceptions
├── py.typed             # Type hint marker
└── api/                 # API endpoint modules
    ├── __init__.py
    ├── projects_api.py
    ├── test_run_executions_api.py
    └── ...
```

### Requirements

Install the development dependencies:

```bash
poetry add --group dev 'datamodel-code-generator[http]' click httpx
```

### Migration from Old Generator

The old OpenAPI Generator (Docker-based) has been removed. The new generator:

1. **No postprocessing needed** - Generates clean code directly
2. **No templates** - Uses datamodel-code-generator
3. **Pydantic v2 native** - No v1 compatibility layer

See the [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/) for code changes.

---

## Other Scripts

- **`check_deps.py`** - Check Python dependencies
- **`run_pytest.sh`** - Run pytest test suite
- **`lint.sh`** - Run linters (mypy, flake8, pylint)
- **`format.sh`** - Format code with black, isort, and flake8
- **`th_cli_install.sh`** - Install CLI tool with pipx
