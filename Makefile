# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                          SIONYX MONOREPO                                  ║
# ║                                                                           ║
# ║  Two apps, one repo:                                                      ║
# ║    • sionyx-kiosk  →  Windows kiosk client (Python/PyQt6)               ║
# ║    • sionyx-web      →  Admin dashboard (React/Vite)                      ║
# ║                                                                           ║
# ║  Naming convention:                                                       ║
# ║    • (no prefix)     →  Desktop client commands                           ║
# ║    • web-*           →  Web admin commands                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# Python 3.12 is required for desktop builds (enforced in build.py)
# Use venv's python - ensure you've activated the venv first
PYTHON := python

.PHONY: help \
        release release-patch release-minor release-major release-dry merge-release sync-branches \
        build build-patch build-minor build-major build-local build-dry version \
        dev dev-debug test test-cov test-fast test-int test-int-cov lint format \
        web-dev web-build web-test web-lint web-deploy web-deploy-hosting \
        merge-feature clean

# ════════════════════════════════════════════════════════════════════════════
#  HELP (default)
# ════════════════════════════════════════════════════════════════════════════

help:
	@echo ""
	@echo "  SIONYX Makefile - Quick Reference"
	@echo "  =================================="
	@echo ""
	@echo "  RELEASE (single command - does everything)"
	@echo "  ------------------------------------------"
	@echo "  make release-minor     Full release: branch → build → merge → tag → push"
	@echo "  make release-patch     Same, for bug fixes (1.1.3 → 1.1.4)"
	@echo "  make release-major     Same, for breaking changes (1.1.3 → 2.0.0)"
	@echo ""
	@echo "  BUILD (if you need to build without releasing)"
	@echo "  ----------------------------------------------"
	@echo "  make build             Build installer"
	@echo "  make build-local       Build without uploading"
	@echo "  make version           Show current version"
	@echo ""
	@echo "  DEVELOPMENT"
	@echo "  -----------"
	@echo "  make dev               Run desktop app"
	@echo "  make test              Run all tests"
	@echo "  make test-cov          Run tests with coverage report"
	@echo "  make test-int          Run integration tests only"
	@echo "  make test-unit         Run unit tests only"
	@echo "  make lint              Check code style"
	@echo "  make format            Auto-fix formatting"
	@echo ""
	@echo "  WEB ADMIN (sionyx-web)"
	@echo "  ----------------------"
	@echo "  make web-dev           Run dev server"
	@echo "  make web-test          Run tests"
	@echo "  make web-deploy        Deploy to Firebase"
	@echo ""
	@echo "  GIT WORKFLOW"
	@echo "  ------------"
	@echo "  make merge-feature     Merge feature branch (with coverage check)"
	@echo ""
	@echo "  For full command list: make help-full"
	@echo ""

help-full:
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║                    SIONYX - Full Command List                  ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  RELEASE (atomic: branch → build → version bump → merge → tag → push)"
	@echo "  release-patch      Patch release (1.1.3 → 1.1.4) - bug fixes"
	@echo "  release-minor      Minor release (1.1.3 → 1.2.0) - new features"
	@echo "  release-major      Major release (1.1.3 → 2.0.0) - breaking changes"
	@echo "  release-dry        Preview what would happen (no changes)"
	@echo ""
	@echo "  Note: Version is only bumped AFTER successful build."
	@echo "        If build fails, everything is rolled back."
	@echo ""
	@echo "BUILD COMMANDS"
	@echo "  build              Build installer (default: patch bump)"
	@echo "  build-patch        Build with patch version bump"
	@echo "  build-minor        Build with minor version bump"
	@echo "  build-major        Build with major version bump"
	@echo "  build-local        Build without uploading (for testing)"
	@echo "  build-dry          Preview what version would be built"
	@echo "  version            Show current version"
	@echo ""
	@echo "  NOTE: Build fails if test coverage drops."
	@echo "        Override with: make build SKIP_COV=true"
	@echo ""
	@echo "DESKTOP APP (sionyx-kiosk)"
	@echo "  dev                Run app"
	@echo "  dev-debug          Run app with DEBUG logging"
	@echo "  test               Run all tests"
	@echo "  test-cov           Run tests with coverage report"
	@echo "  test-int           Run integration tests only (25 tests)"
	@echo "  test-int-cov       Run integration tests with coverage"
	@echo "  test-unit          Run unit tests only (no integration)"
	@echo "  test-fast          Run fast tests only (utils + services)"
	@echo "  test-fail          Run tests, stop on first failure"
	@echo "  lint               Check code style"
	@echo "  lint-fix           Fix code style issues"
	@echo "  format             Full formatting (line endings + black + isort)"
	@echo "  format-check       Check formatting without changes"
	@echo ""
	@echo "WEB ADMIN (sionyx-web)"
	@echo "  web-dev            Run dev server"
	@echo "  web-build          Build for production"
	@echo "  web-preview        Preview production build locally"
	@echo "  web-test           Run tests (watch mode)"
	@echo "  web-test-run       Run tests once"
	@echo "  web-test-cov       Run tests with coverage"
	@echo "  web-lint           Check code style"
	@echo "  web-deploy         Deploy all (hosting + functions + database)"
	@echo "  web-deploy-hosting Deploy hosting only"
	@echo "  web-deploy-functions Deploy functions only"
	@echo "  web-deploy-database Deploy database rules only"
	@echo ""
	@echo "GIT WORKFLOW"
	@echo "  merge-feature      Merge feature branch to main (coverage check)"
	@echo "  merge-release      Merge release branch to main (create tag)"
	@echo "  sync-branches      Create release branches for tags that don't have them"
	@echo ""
	@echo "OTHER"
	@echo "  lint-all           Lint both apps"
	@echo "  clean              Remove build artifacts"
	@echo ""

# ════════════════════════════════════════════════════════════════════════════
#  RELEASE WORKFLOW
#  
#  Single command does everything:
#    make release-minor
#  
#  This will:
#    1. Create release/1.2.0 branch
#    2. Bump version in version.json
#    3. Build installer (runs tests with coverage check)
#    4. Merge back to main
#    5. Create git tag v1.2.0
#    6. Push to remote
# ════════════════════════════════════════════════════════════════════════════

release: release-patch

release-patch:
	@$(PYTHON) scripts/release.py --patch

release-minor:
	@$(PYTHON) scripts/release.py --minor

release-major:
	@$(PYTHON) scripts/release.py --major

release-dry:
	@$(PYTHON) scripts/release.py --patch --dry-run

# Sync release branches with tags (create missing branches)
sync-branches:
	@$(PYTHON) scripts/sync_release_branches.py

merge-release:
	@$(PYTHON) scripts/merge_release.py

# ════════════════════════════════════════════════════════════════════════════
#  BUILD COMMANDS
# ════════════════════════════════════════════════════════════════════════════

# Coverage check can be skipped with: make build SKIP_COV=true
SKIP_COV_FLAG := $(if $(SKIP_COV),--skip-coverage-check,)

version:
	@$(PYTHON) -c "import json; v=json.load(open('sionyx-kiosk/version.json')); print(f\"SIONYX v{v['version']} (Build #{v.get('buildNumber', 1)})\")"

build: build-patch

build-patch:
	@echo "Building installer (patch version)..."
	cd sionyx-kiosk && $(PYTHON) build.py --patch $(SKIP_COV_FLAG)

build-minor:
	@echo "Building installer (minor version)..."
	cd sionyx-kiosk && $(PYTHON) build.py --minor $(SKIP_COV_FLAG)

build-major:
	@echo "Building installer (major version)..."
	cd sionyx-kiosk && $(PYTHON) build.py --major $(SKIP_COV_FLAG)

build-local:
	@echo "Building installer locally (no upload)..."
	cd sionyx-kiosk && $(PYTHON) build.py --no-upload --keep-local $(SKIP_COV_FLAG)

build-dry:
	@echo "Dry run - previewing version changes..."
	cd sionyx-kiosk && $(PYTHON) build.py --dry-run

# ════════════════════════════════════════════════════════════════════════════
#  DESKTOP APP - Development
# ════════════════════════════════════════════════════════════════════════════

dev:
	@echo "Starting desktop app..."
	cd sionyx-kiosk && $(PYTHON) src/main.py

run: dev

dev-debug:
	@echo "Starting desktop app (DEBUG mode)..."
	cd sionyx-kiosk && $(PYTHON) src/main.py --verbose

run-debug: dev-debug

# ════════════════════════════════════════════════════════════════════════════
#  DESKTOP APP - Testing
# ════════════════════════════════════════════════════════════════════════════

test:
	@echo "Running tests..."
	cd sionyx-kiosk && $(PYTHON) -m pytest src/ -v

test-cov:
	@echo "Running tests with coverage..."
	cd sionyx-kiosk && $(PYTHON) -m pytest src/ -v --cov=src --cov-report=term-missing

test-fast:
	@echo "Running fast tests (utils + services)..."
	cd sionyx-kiosk && $(PYTHON) -m pytest src/utils/ src/services/ -v

test-fail:
	@echo "Running tests (stop on first failure)..."
	cd sionyx-kiosk && $(PYTHON) -m pytest src/ -v -x

test-int:
	@echo "Running integration tests..."
	cd sionyx-kiosk && $(PYTHON) -m pytest src/tests/integration/ -v

test-int-cov:
	@echo "Running integration tests with coverage..."
	cd sionyx-kiosk && $(PYTHON) -m pytest src/tests/integration/ -v --cov=src --cov-report=term-missing

test-unit:
	@echo "Running unit tests only (excluding integration)..."
	cd sionyx-kiosk && $(PYTHON) -m pytest src/ -v --ignore=src/tests/integration/

# Run specific test file: make test-file FILE=src/services/auth_service_test.py
test-file:
	cd sionyx-kiosk && $(PYTHON) -m pytest $(FILE) -v

# Run tests matching pattern: make test-match PATTERN=test_login
test-match:
	cd sionyx-kiosk && $(PYTHON) -m pytest src/ -v -k "$(PATTERN)"

# ════════════════════════════════════════════════════════════════════════════
#  DESKTOP APP - Code Quality
# ════════════════════════════════════════════════════════════════════════════

lint:
	@echo "Checking code style..."
	@cd sionyx-kiosk && $(PYTHON) -m black --check src/ || (echo "Run 'make lint-fix' to fix." && exit 1)
	@cd sionyx-kiosk && $(PYTHON) -m isort --check-only src/ || (echo "Run 'make lint-fix' to fix." && exit 1)
	@cd sionyx-kiosk && $(PYTHON) -m flake8 src/ --config=.flake8 || (echo "flake8 errors - fix manually." && exit 1)
	@echo "OK!"

lint-fix:
	@echo "Fixing code style..."
	@cd sionyx-kiosk && $(PYTHON) -m black src/
	@cd sionyx-kiosk && $(PYTHON) -m isort src/
	@echo "Done!"

format:
	@echo "Full formatting..."
	@cd sionyx-kiosk && $(PYTHON) format.py src/
	@cd sionyx-kiosk && $(PYTHON) -m black src/
	@cd sionyx-kiosk && $(PYTHON) -m isort src/
	@echo "Done!"

format-check:
	@echo "Checking formatting..."
	@cd sionyx-kiosk && $(PYTHON) format.py --check src/
	@cd sionyx-kiosk && $(PYTHON) -m black --check src/
	@cd sionyx-kiosk && $(PYTHON) -m isort --check-only src/
	@echo "OK!"

# ════════════════════════════════════════════════════════════════════════════
#  WEB ADMIN (sionyx-web)
# ════════════════════════════════════════════════════════════════════════════

web-dev:
	@echo "Starting web dev server..."
	cd sionyx-web && npm run dev

web-build:
	@echo "Building web for production..."
	cd sionyx-web && npm run build

web-preview:
	@echo "Previewing production build..."
	cd sionyx-web && npm run preview

web-test:
	@echo "Running web tests..."
	cd sionyx-web && npm run test

web-test-run:
	@echo "Running web tests (once)..."
	cd sionyx-web && npm run test:run

web-test-cov:
	@echo "Running web tests with coverage..."
	cd sionyx-web && npm run test:coverage

web-test-ui:
	@echo "Running web tests with UI..."
	cd sionyx-web && npm run test:ui

web-lint:
	@echo "Linting web code..."
	cd sionyx-web && npm run lint

web-deploy: web-test-run web-build
	@echo "Deploying to Firebase..."
	firebase deploy

web-deploy-hosting: web-test-run web-build
	@echo "Deploying hosting..."
	firebase deploy --only hosting

web-deploy-functions:
	@echo "Deploying functions..."
	firebase deploy --only functions

web-deploy-database:
	@echo "Deploying database rules..."
	firebase deploy --only database

# ════════════════════════════════════════════════════════════════════════════
#  GIT WORKFLOW
# ════════════════════════════════════════════════════════════════════════════

# Merge feature branch to main (with coverage check)
# - Runs tests with coverage
# - Compares with main branch baseline
# - Only merges if coverage didn't drop
merge-feature:
	@$(PYTHON) scripts/merge_feature.py

# ════════════════════════════════════════════════════════════════════════════
#  UTILITIES
# ════════════════════════════════════════════════════════════════════════════

lint-all: lint web-lint

clean:
	@echo "Cleaning build artifacts..."
	rm -rf sionyx-kiosk/build sionyx-kiosk/dist
	rm -rf sionyx-web/dist sionyx-web/node_modules/.vite
	@echo "Done!"
