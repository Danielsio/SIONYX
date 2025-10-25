# SIONYX Testing Guide

This document provides comprehensive information about testing in the SIONYX project.

## Overview

SIONYX uses a comprehensive testing strategy that includes:
- **Unit Tests**: Test individual functions and methods in isolation
- **Integration Tests**: Test component interactions
- **UI Tests**: Test PyQt6 components and user interactions
- **Mock Tests**: Test with external dependencies mocked

## Test Framework

- **Primary Framework**: pytest
- **PyQt6 Testing**: pytest-qt
- **Mocking**: pytest-mock
- **Coverage**: pytest-cov
- **Code Quality**: black, isort, flake8, mypy, bandit, safety

## Running Tests

### Quick Start

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test types
make test-unit
make test-integration
make test-ui

# Run linting
make lint

# Format code
make format
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/services/test_firebase_client.py

# Run tests with specific markers
pytest -m "unit"
pytest -m "integration"
pytest -m "ui"

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### Using the test runner script

```bash
# Run all tests
python tests/run_tests.py

# Run specific test path
python tests/run_tests.py --path tests/services/

# Run with verbose output
python tests/run_tests.py --verbose

# Run without coverage
python tests/run_tests.py --no-coverage

# Run with specific markers
python tests/run_tests.py --markers "unit"

# Run linting only
python tests/run_tests.py --lint

# Run tests and linting
python tests/run_tests.py --all
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_helpers.py          # Test utilities and mock classes
├── run_tests.py            # Test runner script
├── services/               # Service layer tests
│   ├── __init__.py
│   ├── test_firebase_client.py
│   ├── test_auth_service.py
│   └── test_session_service.py
├── ui/                     # UI layer tests
│   ├── __init__.py
│   └── test_*.py
├── utils/                  # Utility function tests
│   ├── __init__.py
│   ├── test_error_translations.py
│   ├── test_device_info.py
│   └── test_time_formatter.py
└── database/               # Database layer tests
    ├── __init__.py
    └── test_*.py
```

## Test Categories

### Unit Tests
Test individual functions and methods in isolation using mocks for external dependencies.

```python
@pytest.mark.unit
def test_firebase_client_sign_up():
    # Test FirebaseClient.sign_up method
    pass
```

### Integration Tests
Test component interactions and data flow between services.

```python
@pytest.mark.integration
def test_auth_service_login_flow():
    # Test complete login flow
    pass
```

### UI Tests
Test PyQt6 components, signals, and user interactions.

```python
@pytest.mark.ui
def test_main_window_initialization(qtbot):
    # Test UI component initialization
    pass
```

### Mock Tests
Test with external dependencies mocked for isolated testing.

```python
@pytest.mark.mock
def test_firebase_client_with_mock():
    # Test with mocked Firebase responses
    pass
```

## Fixtures and Mocks

### Common Fixtures

- `qapp`: QApplication instance for PyQt6 tests
- `mock_firebase_client`: Mock Firebase client
- `mock_logger`: Mock logger
- `sample_user_data`: Sample user data for testing
- `sample_session_data`: Sample session data for testing

### Mock Classes

- `MockFirebaseClient`: Advanced Firebase client mock
- `MockLocalDatabase`: Local database mock
- `MockComputerService`: Computer service mock
- `MockQObject`: QObject mock with signals

### Builders

- `FirebaseResponseBuilder`: Build Firebase API responses
- `UserDataBuilder`: Build user data objects
- `SessionDataBuilder`: Build session data objects

## Writing Tests

### Basic Test Structure

```python
def test_function_name():
    """Test description"""
    # Arrange
    input_data = "test"
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result == "expected"
```

### Testing PyQt6 Components

```python
def test_qt_component(qtbot):
    """Test PyQt6 component"""
    widget = MyWidget()
    qtbot.addWidget(widget)
    
    # Test signal emission
    with qtbot.waitSignal(widget.signal_name, timeout=1000):
        widget.trigger_signal()
    
    # Test widget properties
    assert widget.property == expected_value
```

### Testing with Mocks

```python
def test_with_mock(mock_firebase_client):
    """Test with mocked dependencies"""
    mock_firebase_client.sign_in.return_value = {"success": True}
    
    result = auth_service.login("user", "pass")
    
    assert result["success"] is True
    mock_firebase_client.sign_in.assert_called_once_with("user", "pass")
```

### Testing Signals

```python
def test_signal_emission(qtbot):
    """Test PyQt6 signal emission"""
    service = SessionService()
    
    with qtbot.waitSignal(service.time_updated, timeout=1000):
        service.start_session(3600)
    
    assert service.is_active is True
```

## Coverage

The project aims for 80%+ code coverage. Coverage reports are generated in HTML format and can be viewed in the `htmlcov/` directory.

```bash
# Generate coverage report
make coverage

# View coverage report
open htmlcov/index.html
```

## Continuous Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Multiple Python versions (3.9, 3.10, 3.11)
- Multiple operating systems (Ubuntu, Windows, macOS)

## Code Quality

The project enforces code quality through:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **bandit**: Security analysis
- **safety**: Dependency vulnerability scanning

## Best Practices

### Test Naming
- Use descriptive test names: `test_firebase_client_sign_up_success`
- Group related tests in classes: `class TestFirebaseClient`
- Use docstrings to describe test purpose

### Test Organization
- One test file per source file
- Mirror source directory structure
- Use appropriate test markers

### Mocking
- Mock external dependencies
- Use realistic mock data
- Verify mock interactions
- Clean up mocks after tests

### Assertions
- Use specific assertions: `assert result["success"] is True`
- Test both success and failure cases
- Verify side effects and state changes

### PyQt6 Testing
- Use `qtbot` for widget testing
- Test signal emissions with `waitSignal`
- Clean up widgets after tests
- Use appropriate timeouts

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `src/` is in Python path
2. **PyQt6 Issues**: Use `qapp` fixture for QApplication
3. **Mock Issues**: Check mock setup and assertions
4. **Signal Testing**: Use appropriate timeouts

### Debug Tips

```bash
# Run single test with verbose output
pytest tests/services/test_firebase_client.py::TestFirebaseClient::test_sign_up -v -s

# Run tests with debugging
pytest --pdb

# Run tests with print statements
pytest -s

# Run tests with specific log level
pytest --log-cli-level=DEBUG
```

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain or improve coverage
4. Follow code quality standards
5. Update this documentation if needed

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-qt Documentation](https://pytest-qt.readthedocs.io/)
- [PyQt6 Testing Guide](https://doc.qt.io/qtforpython/)
- [Python Mocking Guide](https://docs.python.org/3/library/unittest.mock.html)
