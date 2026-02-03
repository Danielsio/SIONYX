# App Design Overview

This document explains the system design of the SIONYX platform, based on the current codebase. The system provides time-based computer access, print budget enforcement, and package purchases for organizations.

## Purpose

SIONYX is a multi-tenant management platform for shared computers. It combines a Windows kiosk client with a web admin dashboard. The platform is designed for settings such as internet cafes, libraries, and coworking spaces where sessions, printing, and payments must be centrally controlled.

## System at a Glance (Diagram)

```
                      +-----------------------+
                      |   Admins (Browser)    |
                      +-----------+-----------+
                                  |
                                  v
                         +--------+---------+
                         |  sionyx-web      |
                         |  React + AntD    |
                         +--------+---------+
                                  |
                                  v
        +-------------------------+-------------------------+
        |           Firebase Realtime DB + Auth             |
        |   organizations/{orgId}/users|packages|...        |
        +-----------+------------------------------+--------+
                    |                              |
                    v                              v
        +-----------+---------+          +---------+-----------+
        | sionyx-kiosk      |          | Cloud Functions     |
        | PyQt6 Windows kiosk |          | Payment callbacks   |
        +-----------+---------+          +---------+-----------+
                    |                              |
                    v                              v
              [Users at PCs]                [Nedarim Plus]
```

## System Components

### Web Admin Dashboard (`sionyx-web`)
- React + Vite + Ant Design UI
- Admin-only authentication with organization ID
- Manage users, packages, computers, messaging, and pricing
- Firebase Realtime Database for all org data
- Firebase Hosting for deployment

Key code references:
- Routing and auth: `sionyx-web/src/App.jsx`
- Pages: `sionyx-web/src/pages/*.jsx`
- Data access: `sionyx-web/src/services/*.js`
- State: `sionyx-web/src/store/*.js`

### Kiosk Client (`sionyx-kiosk`)
- Python 3 + PyQt6 Windows application
- Kiosk mode, session timer, print monitoring
- Uses Firebase REST + SSE for realtime updates
- Local SQLite storage for encrypted credentials

Key code references:
- Entry point: `sionyx-kiosk/src/main.py`
- Session logic: `sionyx-kiosk/src/services/session_service.py`
- Print monitoring: `sionyx-kiosk/src/services/print_monitor_service.py`
- UI pages: `sionyx-kiosk/src/ui/pages/*.py`

### Backend (Firebase)
- Realtime Database is the primary data store
- Firebase Authentication for user/admin auth
- Cloud Functions for payment callbacks

Key code references:
- Cloud Functions: `functions/index.js`
- Database rules: `database.rules.json`

## Data Model (Realtime DB)

All data is scoped under the organization:

```
organizations/{orgId}/
  metadata/
  users/{userId}/
  packages/{packageId}/
  purchases/{purchaseId}/
  computers/{deviceId}/
  messages/{messageId}/
```

This design keeps tenants isolated and lets the desktop and web apps share the same data.

## Flow Diagrams

### 1) Admin Login (Web)
```
Admin -> sionyx-web -> Firebase Auth
  |          |            |
  |          +-> validate orgId + isAdmin
  |          +-> store adminOrgId
```

### 2) User Login + Session Start (Desktop)
```
User -> sionyx-kiosk -> Firebase Auth
  |          |
  |          +-> fetch user under orgId
  |          +-> enforce single session
  |          +-> start local timer (1s)
  |          +-> sync to DB (60s)
  v
[Session Active] -> start print monitor
```

### 3) Print Job Enforcement
```
Print Job -> WMI/Polling -> pause job
                 |
                 +-> get pages + color
                 +-> price = pages * rate
                 +-> check printBalance
                 |        |
                 |        +-> enough? resume + deduct
                 |        +-> not enough? cancel + notify
```

### 4) Package Purchase
```
Desktop UI -> Payment Dialog -> Pending Purchase (DB)
     |               |                |
     |               +-> Nedarim Plus |
     |                                v
     +<-- Cloud Function callback ----+
          (complete + credit time/prints)
```

### 5) Messaging
```
Admin -> Web -> DB(messages)
                     |
                     v
              Desktop SSE listener
                     |
                     v
                 User reads -> DB(read=true)
```

## Core Workflows

### Admin Login (Web)
1. Admin enters phone, password, org ID.
2. Phone is transformed to `{phone}@sionyx.app`.
3. User is verified as `isAdmin`.
4. `adminOrgId` is stored in local storage.

Code: `sionyx-web/src/services/authService.js`

### User Login + Session Start (Desktop)
1. User enters phone + password.
2. Auth via Firebase, user is fetched under `organizations/{orgId}/users/{uid}`.
3. Single-session enforcement checks if user is already active on another computer.
4. Session starts: local countdown (1s) + periodic sync to Firebase (60s).
5. Print monitor starts when session is active.

Code: `sionyx-kiosk/src/services/auth_service.py`, `sionyx-kiosk/src/services/session_service.py`

### Print Job Enforcement (Desktop)
1. Print job detected via WMI event or polling fallback.
2. Job is paused immediately to inspect page count.
3. Cost is computed using org pricing (B/W vs color).
4. If user has budget, cost is deducted and job resumes.
5. If not, job is canceled and user is notified.

Code: `sionyx-kiosk/src/services/print_monitor_service.py`

### Package Purchase Flow
1. User selects a package on the desktop app.
2. Payment dialog opens embedded web gateway.
3. Pending purchase is created in Firebase.
4. Cloud Function callback marks purchase complete and credits time/prints.
5. Desktop listens for purchase completion and refreshes user data.

Code:
- Desktop: `sionyx-kiosk/src/ui/payment_dialog.py`, `sionyx-kiosk/src/services/purchase_service.py`
- Backend: `functions/index.js`

### Messaging
1. Admin sends a message via web dashboard.
2. Desktop app listens via SSE and displays unread messages.
3. User reads messages and updates `read` status in Firebase.

Code:
- Web: `sionyx-web/src/services/chatService.js`
- Desktop: `sionyx-kiosk/src/services/chat_service.py`

## Security and Kiosk Controls (Desktop)

The desktop app enforces kiosk restrictions when enabled:
- Blocks common OS escape keys (Alt+Tab, Win key, etc.)
- Terminates forbidden processes (cmd, regedit, taskmgr)
- Admin exit hotkey with password
- Browser cleanup and process cleanup between sessions

Key code:
- `sionyx-kiosk/src/services/keyboard_restriction_service.py`
- `sionyx-kiosk/src/services/process_restriction_service.py`
- `sionyx-kiosk/src/services/process_cleanup_service.py`
- `sionyx-kiosk/src/services/browser_cleanup_service.py`

## Deployment

- Web: built with Vite and deployed to Firebase Hosting (`make web-deploy-hosting`)
- Desktop: packaged with PyInstaller, installer built with NSIS
- Functions: deployed with Firebase CLI

## Design Rationale

- Realtime DB provides low-latency updates for sessions, purchases, and messages.
- Local countdown reduces database writes while preserving accuracy.
- Org-scoped paths enforce tenant isolation.
- Desktop uses WMI for print monitoring to control billing before print completion.

## Limitations and Risks

- Desktop app is Windows-only.
- Firebase Realtime DB schema changes require coordinated updates across web and desktop.
- Print monitoring depends on Windows spooler behavior; edge cases require careful handling.
- Offline usage is limited to local countdown until sync resumes.

## Related Files Index

- Web entry: `sionyx-web/src/main.jsx`
- Desktop entry: `sionyx-kiosk/src/main.py`
- Admin UI pages: `sionyx-web/src/pages/*.jsx`
- Desktop UI pages: `sionyx-kiosk/src/ui/pages/*.py`
- Services (web): `sionyx-web/src/services/*.js`
- Services (desktop): `sionyx-kiosk/src/services/*.py`
