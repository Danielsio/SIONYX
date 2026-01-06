# SIONYX Monorepo Makefile
# =========================
# Naming Convention:
#   - No prefix  = Client app (sionyx-desktop)
#   - web-*      = Web admin (sionyx-web)
#
# Examples:
#   make dev      → run client
#   make web-dev  → run web admin
#   make test     → test client
#   make web-lint → lint web admin

.PHONY: help dev dev-debug run run-debug test test-cov test-fast test-fail lint lint-fix format format-check build build-patch build-minor build-major build-dry build-local version clean \
        web-dev web-build web-preview web-lint web-test web-test-run web-test-cov web-test-ui web-deploy web-deploy-hosting web-deploy-functions web-deploy-database

# Default target
help:
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║                    SIONYX Monorepo                             ║"
	@echo "╠════════════════════════════════════════════════════════════════╣"
	@echo "║  (no prefix) = Client App (sionyx-desktop)                     ║"
	@echo "║  web-*       = Web Admin (sionyx-web)                          ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Client App Commands:"
	@echo "  dev             - Run client app"
	@echo "  dev-debug       - Run client app with DEBUG logging"
	@echo "  test            - Run tests (co-located in src/)"
	@echo "  test-cov        - Run tests with coverage"
	@echo "  test-fast       - Run fast tests (utils + services)"
	@echo "  test-fail       - Run tests, stop on first failure"
	@echo "  format          - Fix line endings + trailing newlines + black + isort"
	@echo "  format-check    - Check formatting without changing files"
	@echo "  lint            - Check code style"
	@echo "  lint-fix        - Fix code style (use 'format' for full formatting)"
	@echo "  build           - Build installer (patch version, runs tests with coverage)"
	@echo "  build-minor     - Build installer (minor version, runs tests with coverage)"
	@echo "  build-major     - Build installer (major version, runs tests with coverage)"
	@echo "  build-dry       - Preview version changes"
	@echo "  build-local     - Build without uploading (runs tests with coverage)"
	@echo ""
	@echo "  NOTE: Build fails if test coverage drops. Use SKIP_COV=true to override:"
	@echo "        make build SKIP_COV=true"
	@echo "  version         - Show current version"
	@echo ""
	@echo "Web Admin Commands:"
	@echo "  web-dev         - Run dev server"
	@echo "  web-build       - Build for production"
	@echo "  web-preview     - Preview production build"
	@echo "  web-lint        - Lint code"
	@echo "  web-test        - Run tests"
	@echo "  web-test-cov    - Run tests with coverage"
	@echo "  web-test-ui     - Run tests with UI"
	@echo "  web-deploy      - Deploy all to Firebase"
	@echo "  web-deploy-hosting   - Deploy hosting only"
	@echo "  web-deploy-functions - Deploy functions only"
	@echo "  web-deploy-database  - Deploy database rules only"
	@echo ""
	@echo "Both Apps:"
	@echo "  lint-all        - Lint both apps"
	@echo "  clean           - Clean build artifacts"
	@echo ""

# ============================================================================
# Client App Commands (sionyx-desktop)
# ============================================================================

# Run client app
dev:
	@echo "Starting client app..."
	cd sionyx-desktop && python src/main.py

run: dev

# Run client app with debug logging
dev-debug:
	@echo "Starting client app (DEBUG mode)..."
	cd sionyx-desktop && python src/main.py --verbose

run-debug: dev-debug

# Run tests (co-located in src/)
test:
	@echo "Running client tests..."
	cd sionyx-desktop && pytest src/ -v

# Run tests with coverage
test-cov:
	@echo "Running client tests with coverage..."
	cd sionyx-desktop && pytest src/ -v --cov=src --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "Coverage report: sionyx-desktop/htmlcov/index.html"

# Run fast tests (utils + services only)
test-fast:
	@echo "Running fast tests (utils + services)..."
	cd sionyx-desktop && pytest src/utils/ src/services/ -v -k "test_"

# Run tests, stop on first failure
test-fail:
	@echo "Running client tests (stop on first failure)..."
	cd sionyx-desktop && pytest src/ -v -x

# Run specific test file (usage: make test-file FILE=src/services/test_auth_service.py)
test-file:
	@echo "Running tests in $(FILE)..."
	cd sionyx-desktop && pytest $(FILE) -v

# Run tests matching pattern (usage: make test-match PATTERN=test_login)
test-match:
	@echo "Running tests matching '$(PATTERN)'..."
	cd sionyx-desktop && pytest src/ -v -k "$(PATTERN)"

# Lint client code
lint:
	@echo "Checking client code style..."
	@cd sionyx-desktop && black --check src/ || (echo "Run 'make lint-fix' to fix." && exit 1)
	@cd sionyx-desktop && isort --check-only src/ || (echo "Run 'make lint-fix' to fix." && exit 1)
	@cd sionyx-desktop && flake8 src/ --config=.flake8 || (echo "flake8 check failed." && exit 1)
	@echo "Client code style OK!"

# Fix client code style
lint-fix:
	@echo "Fixing client code style..."
	@cd sionyx-desktop && black src/
	@cd sionyx-desktop && isort src/
	@cd sionyx-desktop && flake8 src/ --config=.flake8 || (echo "flake8 check failed - fix manually." && exit 1)
	@echo "Client code style fixed!"

# Format all files (line endings + trailing newlines + black + isort)
format:
	@echo "Formatting client code..."
	@echo "Step 1/3: Fixing line endings and trailing newlines..."
	@cd sionyx-desktop && python format.py src/
	@echo "Step 2/3: Running black..."
	@cd sionyx-desktop && black src/
	@echo "Step 3/3: Running isort..."
	@cd sionyx-desktop && isort src/
	@echo ""
	@echo "All formatting complete!"

# Check formatting without changing files
format-check:
	@echo "Checking client code formatting..."
	@cd sionyx-desktop && python format.py --check src/
	@cd sionyx-desktop && black --check src/
	@cd sionyx-desktop && isort --check-only src/
	@echo "All formatting checks passed!"

# Show version
version:
	@python -c "import json; v=json.load(open('sionyx-desktop/version.json')); print(f\"SIONYX v{v['version']} (Build #{v.get('buildNumber', 1)})\")"

# Build installer (patch version - default)
# Tests with coverage are now run by build.py, no separate test dependency needed
# Use SKIP_COV=true to skip coverage regression check (e.g., make build SKIP_COV=true)
SKIP_COV_FLAG := $(if $(SKIP_COV),--skip-coverage-check,)

build: build-patch

build-patch:
	@echo "Building client (patch version)..."
	cd sionyx-desktop && python build.py --patch $(SKIP_COV_FLAG)

build-minor:
	@echo "Building client (minor version)..."
	cd sionyx-desktop && python build.py --minor $(SKIP_COV_FLAG)

build-major:
	@echo "Building client (major version)..."
	cd sionyx-desktop && python build.py --major $(SKIP_COV_FLAG)

build-dry:
	@echo "Dry run - previewing version changes..."
	cd sionyx-desktop && python build.py --dry-run

build-local:
	@echo "Building client locally (no upload)..."
	cd sionyx-desktop && python build.py --no-upload --keep-local $(SKIP_COV_FLAG)

# ============================================================================
# Web Admin Commands (sionyx-web)
# ============================================================================

# Run web dev server
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

# Lint web code
web-lint:
	@echo "Linting web admin code..."
	cd sionyx-web && npm run lint

# Run web tests
web-test:
	@echo "Running web admin tests..."
	cd sionyx-web && npm run test

# Run web tests with coverage
web-test-cov:
	@echo "Running web admin tests with coverage..."
	cd sionyx-web && npm run test:coverage

# Run web tests with UI
web-test-ui:
	@echo "Running web admin tests with UI..."
	cd sionyx-web && npm run test:ui

# Deploy to Firebase (runs tests first)
web-deploy: web-test-run web-build
	@echo "Deploying all Firebase services..."
	firebase deploy

web-deploy-hosting: web-test-run web-build
	@echo "Deploying Firebase Hosting..."
	firebase deploy --only hosting

# Run tests without watch mode (for CI/deploy)
web-test-run:
	@echo "Running web admin tests..."
	cd sionyx-web && npm run test:run

web-deploy-functions:
	@echo "Deploying Firebase Functions..."
	firebase deploy --only functions

web-deploy-database:
	@echo "Deploying Firebase Database Rules..."
	firebase deploy --only database

# ============================================================================
# Both Apps
# ============================================================================

# Lint both apps
lint-all: lint web-lint

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf sionyx-desktop/build sionyx-desktop/dist
	rm -rf sionyx-web/dist sionyx-web/node_modules/.vite
	@echo "Clean complete!"
