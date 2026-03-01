# SIONYX - Collaborator Guide

Everything you need to clone, run, build, test, and deploy the SIONYX platform.

---

## Repository Structure

```
SIONYX/
├── sionyx-kiosk-wpf/       # Windows kiosk app (C#/WPF/.NET 8)
│   ├── src/SionyxKiosk/     # Application source
│   ├── tests/               # Unit tests + E2E tests (FlaUI)
│   ├── installer/           # WiX MSI installer project
│   ├── build.ps1            # Build script
│   └── release.ps1          # Release script
├── sionyx-web/              # Admin dashboard (React/Vite)
├── functions/               # Firebase Cloud Functions (Node.js)
├── .github/workflows/       # CI pipeline (GitHub Actions)
├── firebase.json            # Firebase project config
├── database.rules.json      # Firebase RTDB rules
├── storage.rules            # Firebase Storage rules
├── Makefile                 # All build/test/deploy commands
└── .env                     # Environment variables (not in git)
```

---

## Prerequisites

Install these before anything else:

| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| **.NET 8 SDK** | 8.0+ | Build kiosk app + installer | [dotnet.microsoft.com](https://dotnet.microsoft.com/download/dotnet/8.0) |
| **Node.js** | 22+ | Web app + Cloud Functions | [nodejs.org](https://nodejs.org/) |
| **npm** | 10+ | Package manager (comes with Node) | — |
| **Python** | 3.10+ | Upload script (Firebase Storage) | [python.org](https://www.python.org/) |
| **WiX Toolset** | 5.x | Create Windows MSI installer | `dotnet tool install -g wix` |
| **Firebase CLI** | latest | Deploy hosting, functions, rules | `npm install -g firebase-tools` |
| **Make** | any | Run Makefile commands | Pre-installed on most systems; on Windows use `choco install make` |
| **Git** | 2.x | Version control | [git-scm.com](https://git-scm.com/) |

---

## 1. Clone & Setup

### Clone the repo

```powershell
git clone <repo-url> SIONYX
cd SIONYX
```

### Get the secrets (from project lead)

You need two files that are **never committed to git**:

| File | Location | Purpose |
|------|----------|---------|
| `.env` | repo root | Firebase config, org ID, API keys |
| `serviceAccountKey.json` | repo root | Firebase Admin SDK credentials |

The `.env` file contains:

```env
# Organization
ORG_ID=sionov

# Firebase (used by kiosk app)
FIREBASE_API_KEY=...
FIREBASE_AUTH_DOMAIN=...
FIREBASE_PROJECT_ID=...
FIREBASE_DATABASE_URL=...
FIREBASE_STORAGE_BUCKET=...

# Payment callback
NEDARIM_CALLBACK_URL=...

# Firebase (used by web app - same values, VITE_ prefix)
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_DATABASE_URL=...
VITE_FIREBASE_STORAGE_BUCKET=...
```

The `serviceAccountKey.json` is a Firebase service account key. Generate one from [Firebase Console](https://console.firebase.google.com/) > Project Settings > Service Accounts > Generate New Private Key.

> **Important**: Both files are in `.gitignore`. Never commit them.

### Firebase CLI login

```powershell
firebase login
firebase use sionyx-19636
```

### Install dependencies

```powershell
# Web app
cd sionyx-web
npm install

# Cloud Functions
cd ../functions
npm install

# Kiosk app (.NET restore happens automatically on build)
cd ../sionyx-kiosk-wpf
dotnet restore

# Python (for upload script)
pip install firebase-admin
```

---

## 2. Kiosk App (WPF)

Located in `sionyx-kiosk-wpf/`. A C#/WPF/.NET 8 Windows desktop app.

### Architecture

- **MVVM** with CommunityToolkit.Mvvm
- **DI** via Microsoft.Extensions.Hosting (singleton services, reinitialize per user via `.Reinitialize(userId)`)
- **Firebase** Realtime Database for all data, Firebase Auth for login

### Run in development

```powershell
make run
```

The app reads Firebase config from `sionyx-kiosk-wpf/.env` (kiosk-specific) or falls back to the root `.env`.

### Run tests

```powershell
make test              # Unit tests (safe, excludes destructive + E2E)
make test-cov          # Tests + coverage report (HTML)
make e2e               # E2E tests (launches app, needs display)
```

Coverage report opens at `sionyx-kiosk-wpf/coverage-report/index.html`.

#### Test safety

Tests tagged `[Trait("Category", "Destructive")]` interact with system processes and **will crash running applications**. The developer's machine should have `DEVMODE=true` as a user-level environment variable. Destructive tests auto-skip when `DEVMODE=true`, so `dotnet test` without filters is safe on dev machines.

E2E tests are tagged `[Trait("Category", "E2E")]` and use FlaUI for UI automation. They launch the kiosk app and interact with it programmatically. Run them with `make e2e`.

### Build the installer (MSI)

The project uses **WiX Toolset v5** to create a native 64-bit MSI installer. The build process: run tests → `dotnet publish` → WiX creates `.msi` → upload to Firebase Storage.

```powershell
make build             # Full build (tests + installer + upload)
make build-local       # Build installer without uploading
make build-dry         # Preview what would happen (no changes)
```

**Requirements for upload**: `serviceAccountKey.json` must exist in the project root. The upload script (`upload_release.py`) uses `firebase-admin` Python SDK to upload the installer to Firebase Storage and update the RTDB with release metadata.

Output: `sionyx-kiosk-wpf/sionyx-installer-v{VERSION}.msi`

### Release a new version

Releases are atomic: create branch → build → commit → merge to main → tag → push.

```powershell
make release-patch     # Bug fix:      3.0.7 → 3.0.8
make release-minor     # New feature:  3.0.7 → 3.1.0
make release-major     # Breaking:     3.0.7 → 4.0.0
```

This calls `release.ps1` which handles everything. You must be on `main` with no uncommitted changes.

> **Never bump `version.json` manually.** The build and release scripts handle it.
> **Version tags are ONLY for the kiosk app** (e.g., `v2.1.3`). The web app has no version tags -- it always deploys the latest pushed code.

### Key files

| File | Purpose |
|------|---------|
| `version.json` | Current version + build number (auto-managed) |
| `build.ps1` | Build script (test → publish → WiX → upload) |
| `release.ps1` | Release script (branch → build → merge → tag → push) |
| `installer/` | WiX MSI installer project |
| `upload_release.py` | Uploads installer to Firebase Storage |
| `coverage.runsettings` | Test coverage exclusion config |
| `src/SionyxKiosk/` | Application source code |
| `tests/SionyxKiosk.Tests/` | Unit tests (xUnit + FluentAssertions) |
| `tests/SionyxKiosk.E2E/` | E2E tests (FlaUI UI automation) |

---

## 3. Web App (Admin Dashboard)

Located in `sionyx-web/`. A React + Vite admin dashboard.

### Architecture

- **State management**: Zustand stores
- **UI**: Ant Design
- **Org context**: always use `useOrgId()` hook, include `orgId` in `useEffect` deps

### Run in development

```powershell
make web-dev
```

Opens at `http://localhost:5173`. The app reads Firebase config from `VITE_*` environment variables in the root `.env`.

### Run tests

```powershell
make web-test          # Watch mode
```

Or directly:

```powershell
cd sionyx-web
npm run test           # Watch mode
npm run test:run       # Run once
npm run test:coverage  # With coverage
```

Tests use Vitest + @testing-library/react (jsdom, no system side effects -- always safe to run).

### Lint

```powershell
cd sionyx-web
npx eslint .
```

### Build for production

```powershell
cd sionyx-web
npm run build
```

Output goes to `sionyx-web/dist/` (served by Firebase Hosting).

### Deploy

```powershell
# Full deploy (tests + build + deploy hosting + database rules + functions)
make web-deploy

# Hosting only (faster, skips tests)
make web-deploy-hosting
```

**Requirement**: You must be logged in to Firebase CLI (`firebase login`) and have deploy permissions on the project.

---

## 4. Cloud Functions

Located in `functions/`. Node.js Cloud Functions for Firebase.

### Run locally

```powershell
cd functions
npm run serve          # Firebase emulator
```

### Deploy

```powershell
firebase deploy --only functions
```

### Functions

| Function | Type | Purpose |
|----------|------|---------|
| `nedarimCallback` | HTTPS | Webhook for Nedarim Plus payment gateway. Called after credit card transactions to update purchase status in RTDB. |
| `registerOrganization` | Callable | Creates a new organization: generates org ID, writes RTDB structure, creates Firebase Auth admin user. |
| `cleanupTestOrganization` | Callable | Deletes a test organization and its associated auth users. Safety guard: only works on org IDs starting with "ci" or "test". Used by CI pipeline. |

---

## 5. CI/CD Pipeline

The project uses **GitHub Actions** for continuous integration. The pipeline runs on every push to `main` and on pull requests.

### Jobs

| Job | Runner | What it does |
|-----|--------|-------------|
| **web-tests** | Ubuntu | `npm ci` → ESLint → Vitest |
| **kiosk-tests** | Windows | `dotnet test` (unit tests, excludes E2E) |
| **installer-test** | Windows | Build MSI → install → verify → uninstall → verify cleanup |
| **kiosk-e2e** | Windows | Create test org → build app → FlaUI smoke + auth flow tests → cleanup test org |

### E2E Test Infrastructure

The `kiosk-e2e` job creates a **dedicated test organization** (`cie2etest`) in Firebase for each run:

1. **Cleanup** any leftover test org from previous runs
2. **Create** a fresh org via `registerOrganization` Cloud Function (dummy Nedarim credentials, hardcoded test phone/password)
3. **Generate** `.env` file with `ORG_ID=cie2etest`
4. **Build** the kiosk app
5. **Run** E2E tests (smoke tests → login → navigation)
6. **Cleanup** the test org (runs even if tests fail)

No GitHub secrets are needed for E2E tests -- all credentials are hardcoded constants for the throwaway test org.

### E2E Test Structure

All E2E tests live in `sionyx-kiosk-wpf/tests/SionyxKiosk.E2E/` and use a shared app instance with priority ordering:

| Priority | Test | What it verifies |
|----------|------|-----------------|
| 1-4 | Smoke tests | App launches, auth window has phone/password/login elements |
| 10 | Login | Types credentials, clicks login, verifies main window appears |
| 20 | Navigation | Clicks through all nav pages (packages, history, print history, help, home) |

---

## 6. Firebase Services

The project uses these Firebase services:

| Service | Purpose |
|---------|---------|
| **Authentication** | User login (phone + password) |
| **Realtime Database** | All app data (users, sessions, packages, purchases, messages, announcements, computers) |
| **Cloud Storage** | Installer `.msi` hosting + release metadata (`latest.json`) |
| **Cloud Functions** | Payment callback, org registration, test cleanup |
| **Hosting** | Admin dashboard web app |

### Deploy rules

```powershell
firebase deploy --only "database"     # RTDB rules
firebase deploy --only "storage"      # Storage rules
firebase deploy --only "hosting"      # Web app
firebase deploy --only "functions"    # Cloud Functions
firebase deploy                       # Everything
```

---

## 7. Quick Reference

### All Makefile commands

```
make help              # Show all commands

# Kiosk
make run               # Run kiosk app
make test              # Run unit tests (safe)
make test-all          # Run ALL tests (including destructive)
make test-cov          # Tests + coverage
make e2e               # Run E2E tests (needs display)
make build             # Build installer + upload
make build-local       # Build installer (no upload)
make build-dry         # Preview build

# Web
make web-dev           # Dev server
make web-test          # Run tests
make web-deploy        # Full deploy
make web-deploy-hosting # Hosting only

# Release
make release-patch     # Patch release
make release-minor     # Minor release
make release-major     # Major release
```

### Common workflows

**"I want to run the kiosk app locally"**
1. Get `.env` and `serviceAccountKey.json` from the project lead
2. Set `DEVMODE=true` as a user-level environment variable
3. `make run`

**"I want to work on the web dashboard"**
1. Get `.env` from the project lead
2. `cd sionyx-web && npm install`
3. `make web-dev`

**"I fixed a bug in the kiosk and want to release"**
1. Write a failing test first (TDD)
2. Implement the fix
3. `make test` (ensure all pass)
4. Commit with clear explanation
5. `make release-patch`

**"I updated the web dashboard and want to deploy"**
1. `make web-deploy`

**"I changed Cloud Functions"**
1. `cd functions && npm run serve` (test locally)
2. `firebase deploy --only functions`

**"I changed database rules"**
1. Edit `database.rules.json`
2. `firebase deploy --only "database"`

---

## 8. Secrets Checklist

Before you can do anything meaningful, make sure you have:

- [ ] `.env` in project root (Firebase config + org settings)
- [ ] `sionyx-kiosk-wpf/.env` (kiosk-specific overrides, optional)
- [ ] `serviceAccountKey.json` in project root (needed for build upload + Cloud Functions)
- [ ] `firebase login` completed
- [ ] Firebase project access granted by project owner
- [ ] `DEVMODE=true` user-level env var set (protects against destructive tests)

Ask the project lead for all of these. They cannot be committed to git.
