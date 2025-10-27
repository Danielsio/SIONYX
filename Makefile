# SIONYX Makefile
# ===============

.PHONY: help test build lint lint-fix run

# Default target
help:
	@echo "SIONYX Development Commands"
	@echo "=========================="
	@echo "  run     - Run the application"
	@echo "  test    - Not implemented yet (placeholder)"
	@echo "  build   - Build the application"
	@echo "  lint    - Run linting checks (without fixing)"
	@echo "  lint-fix - Auto-fix all linting issues"

# Run
run:
	@echo "Starting SIONYX application..."
	python src/main.py

# Testing (not implemented yet)
test:
	@echo "Testing is not implemented yet"
	@echo "This will be built slowly and steadily"

# Build
build:
	@echo "Building application..."
	python build.py

# Code Quality - Check only (no fixing)
lint:
	@echo "Running black..."
	@black --check src/ tests/ || (echo "Black check failed. Run 'make lint-fix' to fix." && exit 1)
	@echo "Running isort..."
	@isort --check-only src/ tests/ || (echo "isort check failed. Run 'make lint-fix' to fix." && exit 1)
	@echo "Running flake8 (ignoring C901 complexity and line length warnings)..."
	@flake8 src/ tests/ --ignore=C901,E501 || (echo "flake8 check failed." && exit 1)

# Code Quality - Auto-fix all issues
lint-fix:
	@echo "Auto-fixing all linting issues..."
	@echo "Running black (fixing)..."
	@black src/ tests/
	@echo "Running isort (fixing)..."
	@isort src/ tests/
	@echo "Running flake8 (ignoring C901 complexity and line length warnings)..."
	@flake8 src/ tests/ --ignore=C901,E501 || (echo "flake8 check failed - fix remaining issues manually." && exit 1)
	@echo ""
	@echo "✓ All linting issues have been auto-fixed!"
