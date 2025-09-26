# Test Suite for th_cli

This directory contains comprehensive test coverage for the Test Harness CLI application.

## Test Structure

The test suite is organized following modern Python testing practices and PEP 8 guidelines:

```
tests/
├── __init__.py                     # Test package initialization
├── conftest.py                     # Shared fixtures and configuration
├── test_abort_testing.py           # Tests for abort-testing command
├── test_available_tests.py         # Tests for available-tests command
├── test_project_commands.py        # Tests for all project commands
├── test_run_tests.py               # Tests for run-tests command
├── test_test_run_execution.py  # Tests for test-run-execution command
├── test_test_runner_status.py      # Tests for test-runner-status command
├── test_utils.py                   # Tests for utility functions
└── README.md                       # This file
```

## Test Categories

Tests are organized into several categories using pytest markers:

- `@pytest.mark.unit` - Unit tests for individual functions/methods
- `@pytest.mark.cli` - CLI command tests using Click's test runner

## Coverage Areas

### Command Tests
Each CLI command has comprehensive test coverage including:
- **Success scenarios** - Normal operation with valid inputs
- **Error handling** - API errors, network failures, invalid inputs
- **Parameter validation** - Required parameters, format validation
- **Output formatting** - JSON vs table output, colorization
- **Help messages** - Command documentation and usage

### Utility Function Tests
Core utility functions are tested for:
- **Configuration handling** - Properties files, PICS XML parsing
- **Data transformation** - Test selection building, config merging
- **Error conditions** - Malformed files, missing data
- **Edge cases** - Empty inputs, circular references

### Integration Tests
End-to-end workflows including:
- **Complete project lifecycle** - Create → List → Update → Delete
- **Test execution flows** - Available tests → Status check → Run tests
- **Error recovery** - Network failures, partial API responses
- **Performance** - Startup time, large outputs, concurrent execution

## Running Tests

### Prerequisites
Ensure you have the development dependencies installed:
```bash
poetry install --with dev
```

Then enter the cli directory in:
```bash
cd certification-tool/cli
```

### Run All Tests
```bash
# Run all tests with coverage
poetry run pytest --cov=th_cli --cov-report=term-missing --cov-report=html

# Run all tests without coverage
poetry run pytest --no-cov

# Run tests in parallel for faster execution
poetry run pytest -n auto --cov=th_cli
```

### Run Specific Test Categories
```bash
# Unit tests only
poetry run pytest -m unit

# CLI command tests only  
poetry run pytest -m cli
```

### Run Tests for Specific Commands
```bash
# Test specific command
poetry run pytest tests/test_abort_testing.py

# Test specific function
poetry run pytest tests/test_utils.py::TestBuildTestSelection::test_build_test_selection_success
```

### Debugging Tests
```bash
# Run with verbose output
poetry run pytest -v

# Stop at first failure
poetry run pytest -x

# Show local variables in tracebacks
poetry run pytest -l

# Run specific test with debug output
poetry run pytest -s tests/test_run_tests.py::TestRunTestsCommand::test_run_tests_success_minimal_args
```

### Pytest Script
```bash
# Alternatively, run the pytest script with any required argument
./scripts/run_pytest.py -m cli --no-cov
```

## Test Configuration

### pytest Configuration
Test configuration is defined in `pyproject.toml`:
- **Coverage target**: 85% minimum
- **Test discovery**: Automatic for `test_*.py` files
- **Markers**: Custom markers for test categorization
- **Output formats**: Terminal, HTML, and XML coverage reports

### Fixtures and Mocks
The `conftest.py` file provides:
- **CLI runner**: Click test runner for command testing
- **Mock API clients**: Async and sync API mocks
- **Sample data**: Test collections, projects, configurations
- **Temporary files**: Config files, PICS directories
- **Color management**: Consistent output for testing

## Test Design Principles

### 1. Isolation
- Each test is independent and doesn't rely on external services
- Comprehensive mocking of API clients and external dependencies
- Temporary directories for file-based tests

### 2. Comprehensive Coverage
- **Happy path testing** - Normal successful operations
- **Error path testing** - All error conditions and edge cases
- **Parameter validation** - Input validation and sanitization
- **Output verification** - Correct formatting and content

### 3. Maintainability
- **Clear test names** - Descriptive test method names
- **Parameterized tests** - Reduce duplication for similar scenarios
- **Shared fixtures** - Reusable test data and setup
- **Documentation** - Docstrings explaining test purpose

### 4. Performance
- **Fast execution** - Mocked external dependencies
- **Parallel execution** - Tests can run concurrently
- **Efficient setup** - Minimal fixture overhead

## Security Testing

The test suite includes security-focused tests:
- **Path traversal prevention** - File path validation
- **Input sanitization** - Malicious input handling  
- **Configuration validation** - Secure defaults and validation

## Continuous Integration

These tests are designed to run in CI environments:
- **No external dependencies** - All API calls mocked
- **Deterministic** - Consistent results across environments
- **Fast execution** - Suitable for rapid feedback cycles
- **Comprehensive reporting** - Coverage and test result reporting

## Adding New Tests

When adding new functionality to th_cli:

1. **Create unit tests** for new functions/methods
2. **Add CLI tests** for new commands or options
3. **Maintain coverage** - Ensure new code is tested
4. **Follow naming conventions** - Use descriptive test names
5. **Add fixtures** to conftest.py for reusable test data

### Test Naming Convention
```python
def test_<function_name>_<scenario>_<expected_outcome>(self):
    """Test <description of what is being tested>."""
```

Example:
```python
def test_create_project_success_with_custom_config(self):
    """Test successful project creation with custom configuration file."""
```

## Coverage Goals

Target coverage metrics:
- **Overall coverage**: ≥85%
- **Command coverage**: 100% of CLI commands tested
- **Error path coverage**: All exception paths tested
- **Branch coverage**: All conditional branches tested

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure th_cli package is installed in development mode
2. **Mock failures**: Check that API mocks match actual API signatures
3. **File permission errors**: Tests create temporary files - ensure write permissions
4. **Async test issues**: Use `pytest-asyncio` for async command testing

### Debug Tips

1. **Use print statements** in tests for debugging (remove before commit)
2. **Check fixture scope** - Ensure fixtures have appropriate scope
3. **Verify mock calls** - Use `assert_called_with()` to verify mock usage
4. **Test isolation** - Run individual tests to isolate issues

## Contributing

When contributing tests:
1. Follow PEP 8 style guidelines
2. Add docstrings to test classes and methods
3. Use type hints where appropriate
4. Ensure tests pass locally before submitting
5. Update this README if adding new test categories or patterns