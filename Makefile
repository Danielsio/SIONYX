# SIONYX Monorepo Makefile
# =========================
# Two applications:
#   - app (sionyx-desktop): PyQt6 desktop client for kiosk PCs
#   - web (sionyx-web): React admin dashboard

.PHONY: help dev web test test-cov test-fast build lint lint-fix clean \
        app-run app-test app-test-cov app-test-fast app-test-fail app-test-file app-test-match \
        app-build app-build-patch app-build-minor app-build-major app-build-dry app-build-local \
        app-lint app-lint-fix app-version \
        web-dev web-build web-preview web-lint \
        web-deploy web-deploy-hosting web-deploy-functions web-deploy-database

# Default target
help:
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║                    SIONYX Monorepo                             ║"
	@echo "╠════════════════════════════════════════════════════════════════╣"
	@echo "║  app-*  = PyQt Desktop Client (sionyx-desktop)                 ║"
	@echo "║  web-*  = React Admin Dashboard (sionyx-web)                   ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Quick Commands (most common):"
	@echo "  make dev          - Run desktop client app"
	@echo "  make web          - Run web admin dev server"
	@echo "  make test         - Run client app tests"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo "  make build        - Build client installer (patch version)"
	@echo "  make lint         - Lint both apps"
	@echo "  make lint-fix     - Auto-fix lint issues in both apps"
	@echo ""
	@echo "Client App Commands (sionyx-desktop):"
	@echo "  app-run           - Run the desktop client"
	@echo "  app-test          - Run all tests"
	@echo "  app-test-cov      - Run tests with coverage"
	@echo "  app-test-fast     - Run fast tests (no Qt/UI)"
	@echo "  app-test-fail     - Run tests, stop on first failure"
	@echo "  app-lint          - Check Python code style"
	@echo "  app-lint-fix      - Auto-fix Python code style"
	@echo "  app-version       - Show current version"
	@echo ""
	@echo "Client Build Commands:"
	@echo "  app-build         - Build with patch increment (1.0.0 -> 1.0.1)"
	@echo "  app-build-minor   - Build with minor increment (1.0.1 -> 1.1.0)"
	@echo "  app-build-major   - Build with major increment (1.1.0 -> 2.0.0)"
	@echo "  app-build-dry     - Preview version changes"
	@echo "  app-build-local   - Build without uploading"
	@echo ""
	@echo "Web Admin Commands (sionyx-web):"
	@echo "  web-dev           - Run dev server"
	@echo "  web-build         - Build for production"
	@echo "  web-preview       - Preview production build"
	@echo "  web-lint          - Lint React code"
	@echo ""
	@echo "Firebase Deployment:"
	@echo "  web-deploy          - Deploy all (hosting + functions + database)"
	@echo "  web-deploy-hosting  - Deploy hosting only"
	@echo "  web-deploy-functions - Deploy functions only"
	@echo "  web-deploy-database - Deploy database rules only"
	@echo ""

# ============================================================================
# Quick Aliases (no prefix - most common actions)
# ============================================================================

# Run client app
dev: app-run

# Run web dev server
web: web-dev

# Run client tests
test: app-test

# Run tests with coverage
test-cov: app-test-cov

# Run fast tests (no Qt)
test-fast: app-test-fast

# Build client installer
build: app-build

# Lint both apps
lint: app-lint web-lint

# Fix lint in both apps
lint-fix: app-lint-fix

# ============================================================================
# Client App Commands (sionyx-desktop - PyQt6)
# ============================================================================

# Run the desktop client
app-run:
	@echo "Starting SIONYX desktop client..."
	cd sionyx-desktop && python src/main.py

# Run all tests
app-test:
	@echo "Running client tests..."
	cd sionyx-desktop && pytest tests/ -v

# Run tests with coverage
app-test-cov:
	@echo "Running client tests with coverage..."
	cd sionyx-desktop && pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "Coverage report: sionyx-desktop/htmlcov/index.html"

# Run specific test file (usage: make app-test-file FILE=tests/utils/test_device_info.py)
app-test-file:
	@echo "Running tests in $(FILE)..."
	cd sionyx-desktop && pytest $(FILE) -v

# Run tests matching pattern (usage: make app-test-match PATTERN=test_translate)
app-test-match:
	@echo "Running tests matching '$(PATTERN)'..."
	cd sionyx-desktop && pytest tests/ -v -k "$(PATTERN)"

# Run tests and stop on first failure
app-test-fail:
	@echo "Running client tests (stop on first failure)..."
	cd sionyx-desktop && pytest tests/ -v -x

# Run fast tests (utils and services only - no Qt)
app-test-fast:
	@echo "Running fast tests (utils + services)..."
	cd sionyx-desktop && pytest tests/utils tests/services -v

# Show current version
app-version:
	@python -c "import json; v=json.load(open('sionyx-desktop/version.json')); print(f\"SIONYX v{v['version']} (Build #{v.get('buildNumber', 1)})\")"

# Build with patch increment (default)
app-build: app-build-patch

app-build-patch:
	@echo "Building client with PATCH increment..."
	cd sionyx-desktop && python build.py --patch

# Build with minor increment
app-build-minor:
	@echo "Building client with MINOR increment..."
	cd sionyx-desktop && python build.py --minor

# Build with major increment
app-build-major:
	@echo "Building client with MAJOR increment..."
	cd sionyx-desktop && python build.py --major

# Dry run - preview version changes
app-build-dry:
	@echo "Dry run - previewing version changes..."
	cd sionyx-desktop && python build.py --dry-run

# Build without uploading
app-build-local:
	@echo "Building client locally (no upload)..."
	cd sionyx-desktop && python build.py --no-upload --keep-local

# Lint Python code (check only)
app-lint:
	@echo "Checking client code style..."
	@cd sionyx-desktop && black --check src/ tests/ || (echo "Run 'make app-lint-fix' to fix." && exit 1)
	@cd sionyx-desktop && isort --check-only src/ tests/ || (echo "Run 'make app-lint-fix' to fix." && exit 1)
	@cd sionyx-desktop && flake8 src/ tests/ --config=.flake8 || (echo "flake8 check failed." && exit 1)
	@echo "Client code style OK!"

# Auto-fix Python code style
app-lint-fix:
	@echo "Fixing client code style..."
	@cd sionyx-desktop && black src/ tests/
	@cd sionyx-desktop && isort src/ tests/
	@cd sionyx-desktop && flake8 src/ tests/ --config=.flake8 || (echo "flake8 check failed - fix manually." && exit 1)
	@echo "Client code style fixed!"

# ============================================================================
# Web Admin Commands (sionyx-web - React)
# ============================================================================

# Run dev server
web-dev:
	@echo "Starting web admin dev server..."
	cd sionyx-web && npm run dev

# Build for production
web-build:
	@echo "Building web admin for production..."
	cd sionyx-web && npm run build

# Preview production build
web-preview:
	@echo "Previewing web admin production build..."
	cd sionyx-web && npm run preview

# Lint React code
web-lint:
	@echo "Linting web admin code..."
	cd sionyx-web && npm run lint

# ============================================================================
# Firebase Deployment Commands
# ============================================================================

# Deploy everything
web-deploy: web-build
	@echo "Deploying all Firebase services..."
	firebase deploy

# Deploy hosting only
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

# ============================================================================
# Utility Commands
# ============================================================================

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf sionyx-desktop/build sionyx-desktop/dist
	rm -rf sionyx-web/dist sionyx-web/node_modules/.vite
	@echo "Clean complete!"
