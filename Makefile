# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                          SIONYX MONOREPO                                  ║
# ║                                                                           ║
# ║  Two apps, one repo:                                                      ║
# ║    • sionyx-kiosk-wpf  →  Windows kiosk client (C#/WPF/.NET 8)          ║
# ║    • sionyx-web         →  Admin dashboard (React/Vite)                   ║
# ║                                                                           ║
# ║  Naming convention:                                                       ║
# ║    • (no prefix)     →  Desktop client commands                           ║
# ║    • web-*           →  Web admin commands                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# Python 3.12 is required for release/merge scripts
PYTHON := python

.PHONY: help \
        release release-patch release-minor release-major release-dry merge-release sync-branches \
        build build-patch build-minor build-major build-local build-dry version \
        dev test test-cov test-fast lint \
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
	@echo "  make release-minor     Full release: branch -> build -> merge -> tag -> push"
	@echo "  make release-patch     Same, for bug fixes (1.1.3 -> 1.1.4)"
	@echo "  make release-major     Same, for breaking changes (1.1.3 -> 2.0.0)"
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
	@echo "  make lint              Check code style (dotnet format)"
	@echo ""
	@echo "  WEB ADMIN (sionyx-web)"
	@echo "  ----------------------"
	@echo "  make web-dev           Run dev server"
	@echo "  make web-test          Run tests"
	@echo "  make web-deploy        Deploy to Firebase"
	@echo ""
	@echo "  GIT WORKFLOW"
	@echo "  ------------"
	@echo "  make merge-feature     Merge feature branch (with test check)"
	@echo ""

help-full:
	@echo ""
	@echo "RELEASE (atomic: branch -> build -> version bump -> merge -> tag -> push)"
	@echo "  release-patch      Patch release (1.1.3 -> 1.1.4) - bug fixes"
	@echo "  release-minor      Minor release (1.1.3 -> 1.2.0) - new features"
	@echo "  release-major      Major release (1.1.3 -> 2.0.0) - breaking changes"
	@echo "  release-dry        Preview what would happen (no changes)"
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
	@echo "DESKTOP APP (sionyx-kiosk-wpf / C# WPF)"
	@echo "  dev                Run app (dotnet run)"
	@echo "  test               Run all tests"
	@echo "  test-cov           Run tests with coverage"
	@echo "  test-fast          Run tests no-build (faster)"
	@echo "  lint               Check code formatting"
	@echo ""
	@echo "WEB ADMIN (sionyx-web)"
	@echo "  web-dev            Run dev server"
	@echo "  web-build          Build for production"
	@echo "  web-preview        Preview production build locally"
	@echo "  web-test           Run tests (watch mode)"
	@echo "  web-test-run       Run tests once"
	@echo "  web-test-cov       Run tests with coverage"
	@echo "  web-lint           Check code style"
	@echo "  web-deploy         Deploy all (hosting + database)"
	@echo "  web-deploy-hosting Deploy hosting only"
	@echo "  web-deploy-database Deploy database rules only"
	@echo ""
	@echo "GIT WORKFLOW"
	@echo "  merge-feature      Merge feature branch to main (test check)"
	@echo "  merge-release      Merge release branch to main (create tag)"
	@echo ""
	@echo "OTHER"
	@echo "  clean              Remove build artifacts"
	@echo ""

# ════════════════════════════════════════════════════════════════════════════
#  RELEASE WORKFLOW
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

sync-branches:
	@$(PYTHON) scripts/sync_release_branches.py

merge-release:
	@$(PYTHON) scripts/merge_release.py

# ════════════════════════════════════════════════════════════════════════════
#  BUILD COMMANDS (WPF)
# ════════════════════════════════════════════════════════════════════════════

version:
	@$(PYTHON) -c "import json; v=json.load(open('sionyx-kiosk-wpf/version.json')); print(f\"SIONYX v{v['version']} (Build #{v.get('buildNumber', 0)})\")"

build: build-patch

build-patch:
	@echo "Building installer (patch version)..."
	cd sionyx-kiosk-wpf && powershell -ExecutionPolicy Bypass -File build.ps1 -Increment patch

build-minor:
	@echo "Building installer (minor version)..."
	cd sionyx-kiosk-wpf && powershell -ExecutionPolicy Bypass -File build.ps1 -Increment minor

build-major:
	@echo "Building installer (major version)..."
	cd sionyx-kiosk-wpf && powershell -ExecutionPolicy Bypass -File build.ps1 -Increment major

build-local:
	@echo "Building installer locally (no upload)..."
	cd sionyx-kiosk-wpf && powershell -ExecutionPolicy Bypass -File build.ps1 -NoUpload

build-dry:
	@echo "Dry run - previewing version changes..."
	cd sionyx-kiosk-wpf && powershell -ExecutionPolicy Bypass -File build.ps1 -DryRun

# ════════════════════════════════════════════════════════════════════════════
#  DESKTOP APP - Development
# ════════════════════════════════════════════════════════════════════════════

dev:
	@echo "Starting desktop app..."
	cd sionyx-kiosk-wpf/src/SionyxKiosk && dotnet run

run: dev

# ════════════════════════════════════════════════════════════════════════════
#  DESKTOP APP - Testing
# ════════════════════════════════════════════════════════════════════════════

test:
	@echo "Running tests..."
	cd sionyx-kiosk-wpf && dotnet test --verbosity normal

test-cov:
	@echo "Running tests with coverage..."
	cd sionyx-kiosk-wpf && dotnet test --collect:"XPlat Code Coverage" --verbosity normal

test-fast:
	@echo "Running tests (no build)..."
	cd sionyx-kiosk-wpf && dotnet test --no-build --verbosity normal

# ════════════════════════════════════════════════════════════════════════════
#  DESKTOP APP - Code Quality
# ════════════════════════════════════════════════════════════════════════════

lint:
	@echo "Checking code formatting..."
	cd sionyx-kiosk-wpf && dotnet format --verify-no-changes --verbosity normal
	@echo "OK!"

lint-fix:
	@echo "Fixing code formatting..."
	cd sionyx-kiosk-wpf && dotnet format
	@echo "Done!"

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

merge-feature:
	@$(PYTHON) scripts/merge_feature.py

# ════════════════════════════════════════════════════════════════════════════
#  UTILITIES
# ════════════════════════════════════════════════════════════════════════════

lint-all: lint web-lint

clean:
	@echo "Cleaning build artifacts..."
	rm -rf sionyx-kiosk-wpf/dist sionyx-kiosk-wpf/src/SionyxKiosk/bin sionyx-kiosk-wpf/src/SionyxKiosk/obj
	rm -rf sionyx-web/dist sionyx-web/node_modules/.vite
	@echo "Done!"
