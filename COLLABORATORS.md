# SIONYX - Collaborator Guide

Everything you need to clone, run, build, test, and deploy the SIONYX platform.

---

## Repository Structure

```
SIONYX/
├── sionyx-kiosk-wpf/    # Windows kiosk app (C#/WPF/.NET 8)
├── sionyx-web/           # Admin dashboard (React/Vite)
├── functions/            # Firebase Cloud Functions (Node.js)
├── firebase.json         # Firebase project config
├── database.rules.json   # Firebase RTDB rules
├── storage.rules         # Firebase Storage rules
├── Makefile              # All build/test/deploy commands
└── .env                  # Environment variables (not in git)
```

---

## Prerequisites

Install these before anything else:

| Tool | Version | Purpose | Install |
|------|---------|---------|---------|
| **.NET 8 SDK** | 8.0+ | Build the kiosk app | [dotnet.microsoft.com](https://dotnet.microsoft.com/download/dotnet/8.0) |
| **Node.js** | 22+ | Web app + Cloud Functions | [nodejs.org](https://nodejs.org/) |
| **npm** | 10+ | Package manager (comes with Node) | — |
| **Python** | 3.10+ | Upload script (Firebase Storage) | [python.org](https://www.python.org/) |
| **NSIS** | 3.x | Create Windows installer | [nsis.sourceforge.io](https://nsis.sourceforge.io/Download) |
| **Firebase CLI** | latest | Deploy hosting, functions, rules | `npm install -g firebase-tools` |
| **Make** | any | Run Makefile commands | Pre-installed on most systems; on Windows use `choco install make` |
| **Git** | 2.x | Version control | [git-scm.com](https://git-scm.com/) |

> **Windows note**: NSIS must be installed at `C:\Program Files (x86)\NSIS`. The build script looks for `makensis.exe` there.

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

# Firebase (used by web app - same values, VITE_ prefix)
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_DATABASE_URL=...
VITE_FIREBASE_STORAGE_BUCKET=...
```

The `serviceAccountKey.json` is a Firebase service account key. You can generate one from the [Firebase Console](https://console.firebase.google.com/) > Project Settings > Service Accounts > Generate New Private Key.

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

### Run in development

```powershell
make run
```

Or directly:

```powershell
cd sionyx-kiosk-wpf/src/SionyxKiosk
dotnet run
```

The app reads Firebase config from `sionyx-kiosk-wpf/.env` (kiosk-specific) or falls back to the root `.env`.

### Run tests

```powershell
make test              # All tests
make test-cov          # Tests + coverage report (HTML)
```

Coverage report opens at `sionyx-kiosk-wpf/coverage-report/index.html`.

### Build the installer

The build process: run tests → `dotnet publish` → copy to dist → NSIS creates `.exe` installer → upload to Firebase Storage.

```powershell
make build             # Full build (tests + installer + upload)
make build-local       # Build installer without uploading
make build-dry         # Preview what would happen (no changes)
```

**Requirements for upload**: `serviceAccountKey.json` must exist in the project root (or set `GOOGLE_APPLICATION_CREDENTIALS` env var). The upload script (`upload_release.py`) uses `firebase-admin` Python SDK to upload the installer to Firebase Storage and update the RTDB with release metadata.

Output: `sionyx-kiosk-wpf/sionyx-installer-v{VERSION}.exe`

### Release a new version

Releases are atomic: create branch → build → commit → merge to main → tag → push.

```powershell
make release-patch     # Bug fix:      3.0.7 → 3.0.8
make release-minor     # New feature:  3.0.7 → 3.1.0
make release-major     # Breaking:     3.0.7 → 4.0.0
```

This calls `release.ps1` which handles everything. You must be on `main` with no uncommitted changes.

> **Never bump `version.json` manually.** The build and release scripts handle it.

### Key files

| File | Purpose |
|------|---------|
| `version.json` | Current version + build number (auto-managed) |
| `build.ps1` | Build script (test → publish → NSIS → upload) |
| `release.ps1` | Release script (branch → build → merge → tag → push) |
| `installer.nsi` | NSIS installer definition |
| `upload_release.py` | Uploads installer to Firebase Storage |
| `coverage.runsettings` | Test coverage exclusion config |
| `src/SionyxKiosk/` | Application source code |
| `tests/SionyxKiosk.Tests/` | Unit tests |

---

## 3. Web App (Admin Dashboard)

Located in `sionyx-web/`. A React + Vite + TypeScript admin dashboard.

### Run in development

```powershell
make web-dev
```

Or directly:

```powershell
cd sionyx-web
npm run dev
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

### Build for production

```powershell
cd sionyx-web
npm run build
```

Output goes to `sionyx-web/dist/` (served by Firebase Hosting).

### Deploy

```powershell
# Full deploy (tests + build + deploy hosting + database rules)
make web-deploy

# Hosting only (faster, skips tests)
make web-deploy-hosting
```

**Requirement**: You must be logged in to Firebase CLI (`firebase login`) and have deploy permissions on the project.

### Key files

| File | Purpose |
|------|---------|
| `src/pages/` | Page components (LandingPage, MessagesPage, etc.) |
| `src/stores/` | Zustand state management |
| `src/services/` | Firebase service layer |
| `src/components/` | Reusable UI components |

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

### Key function

- `nedarimCallback` — Webhook endpoint for the Nedarim Plus payment gateway. Called after a successful credit card transaction to update purchase status in RTDB.

---

## 5. Firebase Services

The project uses these Firebase services:

| Service | Purpose |
|---------|---------|
| **Authentication** | User login (email/password) |
| **Realtime Database** | All app data (users, sessions, packages, purchases, messages) |
| **Cloud Storage** | Installer `.exe` hosting + release metadata (`latest.json`) |
| **Cloud Functions** | Payment callback webhook |
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

## 6. Quick Reference

### All Makefile commands

```
make help              # Show all commands

# Kiosk
make run               # Run kiosk app
make test              # Run tests
make test-cov          # Tests + coverage
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
2. `make run`

**"I want to work on the web dashboard"**
1. Get `.env` from the project lead
2. `cd sionyx-web && npm install`
3. `make web-dev`

**"I fixed a bug in the kiosk and want to release"**
1. Commit your changes to `main`
2. `make test` (ensure all pass)
3. `make release-patch`

**"I updated the web dashboard and want to deploy"**
1. `make web-deploy`

**"I changed Cloud Functions"**
1. `cd functions && npm run serve` (test locally)
2. `firebase deploy --only functions`

**"I changed database rules"**
1. Edit `database.rules.json`
2. `firebase deploy --only "database"`

---

## 7. Secrets Checklist

Before you can do anything meaningful, make sure you have:

- [ ] `.env` in project root (Firebase config + org settings)
- [ ] `sionyx-kiosk-wpf/.env` (kiosk-specific overrides, optional)
- [ ] `serviceAccountKey.json` in project root (needed for build upload + Cloud Functions)
- [ ] `firebase login` completed
- [ ] Firebase project access granted by project owner

Ask the project lead for all of these. They cannot be committed to git.
