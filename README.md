# SIONYX

Kiosk management system with web admin dashboard and WPF desktop app.

## Architecture

> **This is the source of truth for the app's services and how they talk to each other.**
> SIONYX runs entirely on **free tiers** — Firebase **Spark** (Realtime DB, Auth, Hosting) plus a
> **Cloudflare Worker** (`sionyx-server`) that replaces Cloud Functions. **No Blaze, no credit card.**
> The Worker is the only holder of the Firebase service account, so it is the **only writer of
> balances, purchases, and passwords** — money is server-authoritative and clients cannot self-credit.

![SIONYX architecture](docs/architecture.svg)

### Services

| Service | Tech | Role | Cost |
|---|---|---|---|
| **sionyx-web** | React (Vite) | Admin dashboard; reads RTDB, calls the Worker for privileged ops | Firebase Hosting (free) |
| **sionyx-kiosk-wpf** | C# WPF (.NET 8) | Kiosk lockdown, sessions, printing, payments | on-prem |
| **sionyx-server** | Cloudflare Worker (TS) | All privileged logic: payments, password reset, org register, delete-user, balance deduct/adjust, cleanup cron | Workers (free, no card) |
| **Realtime Database** | Firebase | Source of data; rules deny client writes to balances | Spark (free) |
| **Auth** | Firebase | User sign-in; admin ops via the Worker | Spark (free) |
| **Nedarim Plus** | external | Card payments (hosted iframe + server-side saved-card charge) | gateway |
| **GitHub Releases + Actions** | external | Installer hosting; the release workflow publishes `public/latestRelease`; kiosk auto-update verifies SHA-256 and installs via a **SYSTEM scheduled task** (no UAC) | free |
| ~~functions~~ | Firebase Cloud Functions | All six ported to `sionyx-server`; last step is the [callback cutover](docs/CALLBACK-CUTOVER.md), then delete `functions/` (drops Blaze) | — |

### Data flow

```mermaid
flowchart TB
  subgraph clients[Clients]
    web["Web Admin<br/>React · Firebase Hosting"]
    kiosk["Kiosk<br/>WPF · .NET 8 · locked-down PC"]
  end

  worker["<b>sionyx-server</b> · Cloudflare Worker<br/>holds the Firebase service account<br/>— only writer of money —"]

  subgraph fb[Firebase · Spark · free, no card]
    rtdb[("Realtime Database<br/>rules deny client balance writes (C-6)")]
    auth["Authentication"]
  end

  nedarim["Nedarim Plus<br/>payment gateway"]

  subgraph ghp[GitHub · free]
    rel["Releases · MSI installer"]
    act["Actions · CI + Release workflow"]
  end

  %% data + auth
  web -- "read" --> rtdb
  kiosk -- "read · SSE live" --> rtdb
  web -- "sign in" --> auth
  kiosk -- "sign in" --> auth

  %% privileged ops -> Worker (server-authoritative)
  web -- "reset pw · delete user · register org · adjust balance" --> worker
  kiosk -- "deduct time/print · charge saved-card" --> worker

  %% Worker -> Firebase (admin token bypasses rules)
  worker -- "admin writes: balances · purchases · saved-card token" --> rtdb
  worker -- "set password · create / delete user" --> auth
  worker -. "daily cron: cleanup inactive users" .-> rtdb

  %% payments
  kiosk -- "card entry (hosted iframe)" --> nedarim
  worker -- "saved-card charge (ApiPassword server-side)" --> nedarim
  nedarim -- "payment callback (secret) → credit" --> worker

  %% releases + auto-update
  act -- "build MSI · create Release" --> rel
  act -- "publish version + sha256" --> worker
  worker -- "public/latestRelease" --> rtdb
  kiosk -- "poll public/latestRelease" --> rtdb
  rel -- "download MSI" --> kiosk
  kiosk -. "verify SHA-256 → SYSTEM task installs silently" .-> kiosk

  classDef money stroke:#fbbf24,stroke-width:3px;
  class worker money;
```

The deployed Worker: `https://sionyx-server.sionyx-server.workers.dev`.
Migration details + re-fork guide: [SPARK-MIGRATION.md](SPARK-MIGRATION.md) · final ops step: [CALLBACK-CUTOVER.md](docs/CALLBACK-CUTOVER.md).

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
