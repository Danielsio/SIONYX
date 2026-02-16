# SIONYX Monorepo
#
#   sionyx-kiosk-wpf  →  Windows kiosk (C#/WPF/.NET 8)
#   sionyx-web        →  Admin dashboard (React/Vite)
#
# Usage:  make <command>

PYTHON := python

.PHONY: help run test web-dev web-test web-deploy web-deploy-hosting \
        release release-patch release-minor release-major

# ── Help (default) ────────────────────────────────────────────────
help:
	@echo ""
	@echo "  SIONYX"
	@echo "  ======"
	@echo ""
	@echo "  Kiosk (desktop)"
	@echo "    make run              Run the kiosk app"
	@echo "    make test             Run kiosk tests"
	@echo ""
	@echo "  Web (admin dashboard)"
	@echo "    make web-dev          Run web dev server"
	@echo "    make web-test         Run web tests"
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
	cd sionyx-kiosk-wpf && dotnet test --verbosity normal

# ── Web ───────────────────────────────────────────────────────────
web-dev:
	cd sionyx-web && npm run dev

web-test:
	cd sionyx-web && npm run test

web-deploy:
	cd sionyx-web && npm run test:run && npm run build
	firebase deploy

web-deploy-hosting:
	cd sionyx-web && npm run build
	firebase deploy --only hosting

# ── Release ───────────────────────────────────────────────────────
release: release-patch

release-patch:
	@$(PYTHON) scripts/release.py --patch

release-minor:
	@$(PYTHON) scripts/release.py --minor

release-major:
	@$(PYTHON) scripts/release.py --major
