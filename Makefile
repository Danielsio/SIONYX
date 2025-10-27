# SIONYX Makefile
# ===============

.PHONY: help test build build-patch build-minor build-major build-dry lint lint-fix run version \
       web-dev web-build web-preview web-lint web-deploy web-deploy-hosting web-deploy-functions web-deploy-database

# Default target
help:
	@echo "SIONYX Development Commands"
	@echo "=========================="
	@echo ""
	@echo "  run          - Run the application"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting checks"
	@echo "  lint-fix     - Auto-fix linting issues"
	@echo ""
	@echo "Build Commands (with semantic versioning):"
	@echo "  build        - Build with patch increment (1.0.0 -> 1.0.1)"
	@echo "  build-patch  - Same as 'build'"
	@echo "  build-minor  - Build with minor increment (1.0.1 -> 1.1.0)"
	@echo "  build-major  - Build with major increment (1.1.0 -> 2.0.0)"
	@echo "  build-dry    - Preview version changes without building"
	@echo "  build-local  - Build without uploading (for testing)"
	@echo ""
	@echo "  version      - Show current version"
	@echo ""
	@echo "Web (sionyx-web) Commands:"
	@echo "  web-dev             - Run web dev server"
	@echo "  web-build           - Build web for production"
	@echo "  web-preview         - Preview production build"
	@echo "  web-lint            - Lint web code"
	@echo ""
	@echo "Firebase Deployment:"
	@echo "  web-deploy          - Deploy all (hosting + functions + database)"
	@echo "  web-deploy-hosting  - Deploy hosting only"
	@echo "  web-deploy-functions - Deploy functions only"
	@echo "  web-deploy-database - Deploy database rules only"

# Run
run:
	@echo "Starting SIONYX application..."
	python src/main.py

# Testing
test:
	@echo "Running tests..."
	pytest tests/ -v

# Show current version
version:
	@python -c "import json; v=json.load(open('version.json')); print(f\"SIONYX v{v['version']} (Build #{v.get('buildNumber', 1)})\")"

# Build with patch increment (default)
build: build-patch

build-patch:
	@echo "Building with PATCH increment..."
	python build.py --patch

# Build with minor increment (resets patch to 0)
build-minor:
	@echo "Building with MINOR increment..."
	python build.py --minor

# Build with major increment (resets minor and patch to 0)
build-major:
	@echo "Building with MAJOR increment..."
	python build.py --major

# Dry run - show what would happen
build-dry:
	@echo "Dry run - previewing version changes..."
	python build.py --dry-run

# Build without uploading (for local testing)
build-local:
	@echo "Building locally (no upload)..."
	python build.py --no-upload --keep-local

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
	@echo "All linting issues have been auto-fixed!"

# ============================================================================
# Web (sionyx-web) Commands
# ============================================================================

# Run web dev server
web-dev:
	@echo "Starting sionyx-web dev server..."
	cd sionyx-web && npm run dev

# Build web for production
web-build:
	@echo "Building sionyx-web for production..."
	cd sionyx-web && npm run build

# Preview production build locally
web-preview:
	@echo "Previewing sionyx-web production build..."
	cd sionyx-web && npm run preview

# Lint web code
web-lint:
	@echo "Linting sionyx-web..."
	cd sionyx-web && npm run lint

# ============================================================================
# Firebase Deployment Commands
# ============================================================================

# Deploy everything (hosting, functions, database)
web-deploy: web-build
	@echo "Deploying all Firebase services..."
	firebase deploy

# Deploy hosting only (requires build first)
web-deploy-hosting: web-build
	@echo "Deploying Firebase Hosting..."
	firebase deploy --only hosting

# Deploy functions only
web-deploy-functions:
	@echo "Deploying Firebase Functions..."
	firebase deploy --only functions

# Deploy database rules only
web-deploy-database:
	@echo "Deploying Firebase Database Rules..."
	firebase deploy --only database
