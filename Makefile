# SIONYX Monorepo
#
#   sionyx-kiosk-wpf  →  Windows kiosk (C#/WPF/.NET 8)
#   sionyx-web        →  Admin dashboard (React/Vite)
#
# Usage:  make <command>

.PHONY: help run test test-all test-cov e2e build build-local build-dry \
        web-dev web-test web-deploy web-deploy-hosting \
        functions-test test-rules \
        setup-supervisor \
        release release-patch release-minor release-major

# ── Help (default) ────────────────────────────────────────────────
help:
	@echo ""
	@echo "  SIONYX"
	@echo "  ======"
	@echo ""
	@echo "  Kiosk (desktop)"
	@echo "    make run              Run the kiosk app"
	@echo "    make test             Run kiosk tests (skip destructive + e2e)"
	@echo "    make test-all         Run ALL kiosk tests (including destructive)"
	@echo "    make test-cov         Run tests with coverage report"
	@echo "    make e2e              Run E2E tests (launches app, needs display)"
	@echo "    make build            Build installer + upload"
	@echo "    make build-local      Build installer (no upload)"
	@echo "    make build-dry        Preview build (no changes)"
	@echo ""
	@echo "  Cloud Functions"
	@echo "    make functions-test   Run Cloud Functions tests"
	@echo "    make test-rules       Run security rules tests (needs emulator)"
	@echo ""
	@echo "  Supervisor"
	@echo "    make setup-supervisor Setup supervisor user (dry-run by default)"
	@echo ""
	@echo "  Web (admin dashboard)"
	@echo "    make web-dev          Run web dev server"
	@echo "    make web-test         Run web unit tests"
	@echo "    make web-e2e          Run web E2E tests (Playwright)"
	@echo "    make web-deploy       Build + deploy all to Firebase"
	@echo "    make web-deploy-hosting  Deploy hosting only (skip tests)"
	@echo ""
	@echo "  Release (CI/CD)"
	@echo "    make release-patch    Bug fix release   (3.0.0 → 3.0.1)"
	@echo "    make release-minor    Feature release   (3.0.0 → 3.1.0)"
	@echo "    make release-major    Breaking release  (3.0.0 → 4.0.0)"
	@echo ""

# ── Kiosk ─────────────────────────────────────────────────────────
run:
	cd sionyx-kiosk-wpf/src/SionyxKiosk && dotnet run

test:
	cd sionyx-kiosk-wpf && dotnet test --filter "Category!=Destructive&Category!=E2E" --verbosity normal

test-all:
	cd sionyx-kiosk-wpf && dotnet test --verbosity normal

e2e:
	cd sionyx-kiosk-wpf && dotnet build src/SionyxKiosk/SionyxKiosk.csproj
	cd sionyx-kiosk-wpf && dotnet test tests/SionyxKiosk.E2E --verbosity normal

test-cov:
	cd sionyx-kiosk-wpf && dotnet test --filter "Category!=Destructive" --collect:"XPlat Code Coverage" --results-directory TestResults --settings coverage.runsettings --verbosity normal
	cd sionyx-kiosk-wpf && dotnet tool run reportgenerator -reports:"TestResults/**/coverage.cobertura.xml" -targetdir:"coverage-report" -reporttypes:Html
	@echo ""
	@echo "Coverage report: sionyx-kiosk-wpf/coverage-report/index.html"

build:
	cd sionyx-kiosk-wpf && powershell -ExecutionPolicy Bypass -File build.ps1

build-local:
	cd sionyx-kiosk-wpf && powershell -ExecutionPolicy Bypass -File build.ps1 -NoUpload

build-dry:
	cd sionyx-kiosk-wpf && powershell -ExecutionPolicy Bypass -File build.ps1 -DryRun

# ── Cloud Functions ───────────────────────────────────────────────
functions-test:
	cd functions && npm test

# ── Security Rules (requires Firebase emulator) ──────────────────
test-rules:
	cd tests/rules && npm test

# ── Supervisor Setup ─────────────────────────────────────────────
setup-supervisor:
	node scripts/setup-supervisor.js

setup-supervisor-confirm:
	node scripts/setup-supervisor.js --confirm

# ── Web ───────────────────────────────────────────────────────────
web-dev:
	cd sionyx-web && npm run dev

web-test:
	cd sionyx-web && npm run test

web-e2e:
	cd sionyx-web && npx playwright test

web-deploy:
	cd sionyx-web && npm run test:run && npm run build
	firebase deploy

web-deploy-hosting:
	cd sionyx-web && npm run build
	firebase deploy --only hosting

# ── Release (auto-detect from conventional commits) ──────────────
release:
	powershell -ExecutionPolicy Bypass -File scripts/release/release.ps1

release-patch:
	powershell -ExecutionPolicy Bypass -File scripts/release/release.ps1 -Override patch

release-minor:
	powershell -ExecutionPolicy Bypass -File scripts/release/release.ps1 -Override minor

release-major:
	powershell -ExecutionPolicy Bypass -File scripts/release/release.ps1 -Override major

release-dry:
	powershell -ExecutionPolicy Bypass -File scripts/release/release.ps1 -DryRun
