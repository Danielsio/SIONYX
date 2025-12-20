# SIONYX Monorepo Makefile
# =========================
# This repo contains two applications:
#   - sionyx-desktop: PyQt6 desktop client
#   - sionyx-web: React admin dashboard

.PHONY: help install dev run test build lint lint-fix version clean \
        desktop-run desktop-test desktop-build desktop-build-patch desktop-build-minor desktop-build-major \
        desktop-build-dry desktop-build-local desktop-lint desktop-lint-fix desktop-version \
        web-dev web-build web-preview web-lint web-deploy web-deploy-hosting web-deploy-functions web-deploy-database

# Default target
help:
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║                    SIONYX Monorepo                             ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Quick Commands:"
	@echo "  make dev          - Run desktop app (alias for desktop-run)"
	@echo "  make web          - Run web dev server (alias for web-dev)"
	@echo "  make lint         - Lint both apps"
	@echo "  make lint-fix     - Auto-fix lint issues in both apps"
	@echo ""
	@echo "Desktop App (sionyx-desktop) - PyQt6 Client:"
	@echo "  desktop-run       - Run the desktop application"
	@echo "  desktop-test      - Run desktop tests"
	@echo "  desktop-lint      - Lint Python code"
	@echo "  desktop-lint-fix  - Auto-fix Python lint issues"
	@echo "  desktop-version   - Show current version"
	@echo ""
	@echo "Desktop Build Commands (with semantic versioning):"
	@echo "  desktop-build       - Build with patch increment (1.0.0 -> 1.0.1)"
	@echo "  desktop-build-patch - Same as 'desktop-build'"
	@echo "  desktop-build-minor - Build with minor increment (1.0.1 -> 1.1.0)"
	@echo "  desktop-build-major - Build with major increment (1.1.0 -> 2.0.0)"
	@echo "  desktop-build-dry   - Preview version changes without building"
	@echo "  desktop-build-local - Build without uploading"
	@echo ""
	@echo "Web App (sionyx-web) - React Admin Dashboard:"
	@echo "  web-dev           - Run web dev server"
	@echo "  web-build         - Build web for production"
	@echo "  web-preview       - Preview production build"
	@echo "  web-lint          - Lint web code"
	@echo ""
	@echo "Firebase Deployment:"
	@echo "  web-deploy          - Deploy all (hosting + functions + database)"
	@echo "  web-deploy-hosting  - Deploy hosting only"
	@echo "  web-deploy-functions - Deploy functions only"
	@echo "  web-deploy-database - Deploy database rules only"
	@echo ""

# ============================================================================
# Quick Aliases
# ============================================================================

dev: desktop-run

web: web-dev

run: desktop-run

# Lint both apps
lint: desktop-lint web-lint

# Fix lint in both apps
lint-fix: desktop-lint-fix

# ============================================================================
# Desktop App (sionyx-desktop) Commands
# ============================================================================

# Run desktop app
desktop-run:
	@echo "Starting SIONYX desktop application..."
	cd sionyx-desktop && python src/main.py

# Run desktop tests
desktop-test:
	@echo "Running desktop tests..."
	cd sionyx-desktop && pytest tests/ -v

# Show current version
desktop-version:
	@python -c "import json; v=json.load(open('sionyx-desktop/version.json')); print(f\"SIONYX Desktop v{v['version']} (Build #{v.get('buildNumber', 1)})\")"

# Build with patch increment (default)
desktop-build: desktop-build-patch

desktop-build-patch:
	@echo "Building desktop with PATCH increment..."
	cd sionyx-desktop && python build.py --patch

# Build with minor increment (resets patch to 0)
desktop-build-minor:
	@echo "Building desktop with MINOR increment..."
	cd sionyx-desktop && python build.py --minor

# Build with major increment (resets minor and patch to 0)
desktop-build-major:
	@echo "Building desktop with MAJOR increment..."
	cd sionyx-desktop && python build.py --major

# Dry run - show what would happen
desktop-build-dry:
	@echo "Dry run - previewing version changes..."
	cd sionyx-desktop && python build.py --dry-run

# Build without uploading (for local testing)
desktop-build-local:
	@echo "Building desktop locally (no upload)..."
	cd sionyx-desktop && python build.py --no-upload --keep-local

# Desktop Code Quality - Check only (no fixing)
desktop-lint:
	@echo "Linting desktop Python code..."
	@cd sionyx-desktop && black --check src/ tests/ || (echo "Black check failed. Run 'make desktop-lint-fix' to fix." && exit 1)
	@cd sionyx-desktop && isort --check-only src/ tests/ || (echo "isort check failed. Run 'make desktop-lint-fix' to fix." && exit 1)
	@cd sionyx-desktop && flake8 src/ tests/ --config=.flake8 || (echo "flake8 check failed." && exit 1)

# Desktop Code Quality - Auto-fix all issues
desktop-lint-fix:
	@echo "Auto-fixing desktop linting issues..."
	@echo "Running black (fixing)..."
	@cd sionyx-desktop && black src/ tests/
	@echo "Running isort (fixing)..."
	@cd sionyx-desktop && isort src/ tests/
	@echo "Running flake8 (checking)..."
	@cd sionyx-desktop && flake8 src/ tests/ --config=.flake8 || (echo "flake8 check failed - fix remaining issues manually." && exit 1)
	@echo ""
	@echo "Desktop linting issues have been auto-fixed!"

# ============================================================================
# Web App (sionyx-web) Commands
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

# ============================================================================
# Utility Commands
# ============================================================================

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf sionyx-desktop/build sionyx-desktop/dist
	rm -rf sionyx-web/dist sionyx-web/node_modules/.vite
	@echo "Clean complete!"
