# SIONYX Makefile
# ===============

.PHONY: help install install-dev test test-unit test-integration test-ui lint format clean coverage docs

# Default target
help:
	@echo "SIONYX Development Commands"
	@echo "=========================="
	@echo ""
	@echo "Installation:"
	@echo "  install      Install production dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run all tests"
	@echo "  test-unit    Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-ui      Run UI tests only"
	@echo "  coverage     Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint         Run all linting tools"
	@echo "  format       Format code with black and isort"
	@echo ""
	@echo "Utilities:"
	@echo "  clean        Clean up temporary files"
	@echo "  docs         Generate documentation"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Testing
test:
	python -m pytest tests/ -v

test-unit:
	python -m pytest tests/ -m "not integration and not ui" -v

test-integration:
	python -m pytest tests/ -m "integration" -v

test-ui:
	python -m pytest tests/ -m "ui" -v

coverage:
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Code Quality
lint:
	@echo "Running black..."
	black --check src/ tests/
	@echo "Running isort..."
	isort --check-only src/ tests/
	@echo "Running flake8..."
	flake8 src/ tests/
	@echo "Running mypy..."
	mypy src/
	@echo "Running bandit..."
	bandit -r src/
	@echo "Running safety..."
	safety check

format:
	black src/ tests/
	isort src/ tests/

# Utilities
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

docs:
	@echo "Documentation generation not implemented yet"

# Development shortcuts
dev-setup: install-dev
	@echo "Development environment setup complete!"

quick-test:
	python -m pytest tests/ -x -v --tb=short

test-watch:
	python -m pytest tests/ -f -v

# CI/CD helpers
ci-test:
	python -m pytest tests/ --cov=src --cov-report=xml --junitxml=test-results.xml

ci-lint:
	black --check src/ tests/
	isort --check-only src/ tests/
	flake8 src/ tests/
	mypy src/
	bandit -r src/
	safety check
