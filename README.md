# SIONYX

Kiosk management system with web admin dashboard and WPF desktop app.

## Architecture

| Component | Description |
|-----------|-------------|
| **sionyx-web** | React web admin dashboard (Firebase Hosting) |
| **sionyx-kiosk-wpf** | C# WPF desktop app (.NET 8) |
| **functions** | Firebase Cloud Functions (payment callback) |

## Quick Start

### Prerequisites

- Node.js 22+
- .NET 8 SDK
- Firebase CLI

### Web Admin

```bash
cd sionyx-web && npm install && npm run dev
```

### Kiosk

```bash
cd sionyx-kiosk-wpf && dotnet run
```

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make run` | Run kiosk desktop app |
| `make test` | Run kiosk tests |
| `make web-dev` | Run web dev server |
| `make web-test` | Run web tests |
| `make web-deploy` | Build and deploy to Firebase |
| `make release-patch` | Bug fix release (3.0.0 → 3.0.1) |
| `make release-minor` | Feature release (3.0.0 → 3.1.0) |
| `make release-major` | Breaking release (3.0.0 → 4.0.0) |
