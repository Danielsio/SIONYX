# SIONYX Makefile
# ===============

.PHONY: help test build lint run

# Default target
help:
	@echo "SIONYX Development Commands"
	@echo "=========================="
	@echo "  run     - Run the application"
	@echo "  test    - Not implemented yet (placeholder)"
	@echo "  build   - Build the application"
	@echo "  lint    - Run linting checks"

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

# Code Quality
lint:
	@echo "Running black..."
	@black --check src/ tests/ || (echo "Black check failed. Run 'black src/ tests/' to fix." && exit 1)
	@echo "Running isort..."
	@isort --check-only src/ tests/ || (echo "isort check failed. Run 'isort src/ tests/' to fix." && exit 1)
	@echo "Running flake8 (ignoring C901 complexity and line length warnings)..."
	@flake8 src/ tests/ --ignore=C901,E501 || (echo "flake8 check failed." && exit 1)
