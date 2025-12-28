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

.PHONY: help dev run test test-cov test-fast test-fail lint lint-fix build build-patch build-minor build-major build-dry build-local version clean \
        web-dev web-build web-preview web-lint web-test web-test-cov web-test-ui web-deploy web-deploy-hosting web-deploy-functions web-deploy-database

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
	@echo "  test            - Run tests (co-located in src/)"
	@echo "  test-cov        - Run tests with coverage"
	@echo "  test-fast       - Run fast tests (utils + services)"
	@echo "  test-fail       - Run tests, stop on first failure"
	@echo "  lint            - Check code style"
	@echo "  lint-fix        - Fix code style"
	@echo "  build           - Build installer (patch version, runs tests first)"
	@echo "  build-minor     - Build installer (minor version, runs tests first)"
	@echo "  build-major     - Build installer (major version, runs tests first)"
	@echo "  build-dry       - Preview version changes (no tests)"
	@echo "  build-local     - Build without uploading (runs tests first)"
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

# Show version
version:
	@python -c "import json; v=json.load(open('sionyx-desktop/version.json')); print(f\"SIONYX v{v['version']} (Build #{v.get('buildNumber', 1)})\")"

# Build installer (patch version - default)
# All builds depend on tests passing first
build: build-patch

build-patch: test
	@echo "Building client (patch version)..."
	cd sionyx-desktop && python build.py --patch

build-minor: test
	@echo "Building client (minor version)..."
	cd sionyx-desktop && python build.py --minor

build-major: test
	@echo "Building client (major version)..."
	cd sionyx-desktop && python build.py --major

build-dry:
	@echo "Dry run - previewing version changes..."
	cd sionyx-desktop && python build.py --dry-run

build-local: test
	@echo "Building client locally (no upload)..."
	cd sionyx-desktop && python build.py --no-upload --keep-local

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
	@echo ""
	@echo "Coverage report: sionyx-web/coverage/index.html"

# Run web tests with UI
web-test-ui:
	@echo "Running web admin tests with UI..."
	cd sionyx-web && npm run test:ui

# Deploy to Firebase
web-deploy: web-build
	@echo "Deploying all Firebase services..."
	firebase deploy

web-deploy-hosting: web-build
	@echo "Deploying Firebase Hosting..."
	firebase deploy --only hosting

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
