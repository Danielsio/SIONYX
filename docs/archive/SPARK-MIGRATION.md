# SIONYX — Spark-only migration

Goal: run the whole platform on the Firebase **Spark (free)** plan — **no Blaze,
no credit card**. Firebase Cloud Functions and Cloud Storage both require Blaze,
so this migration moves:

1. **All privileged/server logic** → a single **Cloudflare Worker** (`sionyx-server/`).
2. **File hosting** → GitHub Releases (installers) + base64-in-RTDB (small images).

What stays on Spark (all free): **Realtime Database, Authentication, Hosting**.

---

## Architecture

```
Web (React) ──┐  reads/non-privileged writes (tightened RTDB rules)
Kiosk (WPF) ──┼─────────────────────────► Firebase RTDB + Auth  (Spark, free)
              │
              └─ HTTPS ─► sionyx-server (Cloudflare Worker, free, no cold starts)
                          holds the Firebase service account → the ONLY writer of
                          balances / purchases / passwords (money is server-authoritative)
GitHub Releases ─► installer MSIs (auto-update reads RTDB public/latestRelease)
```

The Worker is the only holder of the service account, so balances can never be
self-credited by clients — RTDB rules deny it.

## `sionyx-server` (the Worker)

Replaces all six Cloud Functions. See `sionyx-server/README.md` for full details.

| Endpoint | Replaces | Auth |
|---|---|---|
| `GET /health` | — | none |
| `GET /version/latest` | — | none |
| `POST /payments/nedarim-callback` | `nedarimCallback` | `?secret=` (CALLBACK_SECRET) |
| `POST /auth/reset-password` | `resetUserPassword` | Firebase ID token (admin) |
| `POST /admin/delete-user` | `deleteUser` | Firebase ID token (admin) |
| `POST /org/register` | `registerOrganization` | none (public) |
| `POST /admin/cleanup-test-org` | `cleanupTestOrganization` | `x-sionyx-secret` (ADMIN_SECRET) |
| cron (daily) | `cleanupInactiveUsers` | — |
| `POST /admin/credit` | REMOVED 2026-07-02 — raw balance-minting endpoint; admins use `/admin/adjust-balance` (ID token + role) | — |
| `POST /payments/charge-saved-card` | (planned) saved-card charge | Firebase ID token |

**Deploy:** `wrangler login` → set `[vars]` in `wrangler.toml` → `wrangler secret put`
(FIREBASE_SERVICE_ACCOUNT, ADMIN_SECRET, CALLBACK_SECRET) → `npm run deploy`.

Live (this repo): `https://sionyx-server.sionyx-server.workers.dev`

## Web

`sionyx-web/src/config/firebase.js` exports `SERVER_URL` (override with
`VITE_SERVER_URL`). `registerOrganization`, `resetUserPassword`, `deleteUser`
now call the Worker instead of Cloud Functions.

---

## Cutover checklist (to fully drop Blaze)

- [x] Worker deployed; web admin routed to it.
- [ ] **Point the Nedarim CallBack URL at the Worker**:
      `https://<worker>/payments/nedarim-callback?secret=<CALLBACK_SECRET>`
      (replaces the `…cloudfunctions.net/nedarimCallback` URL in the payment config).
- [ ] Confirm no client still calls a Cloud Function (`grep httpsCallable`).
- [ ] **Delete `functions/`** and remove the Functions block from `firebase.json`.
- [ ] Move installer hosting to GitHub Releases; auto-update reads `public/latestRelease`.
- [ ] Migrate any Firebase Storage image use to base64-in-RTDB (R2 needs a card).
- [ ] Downgrade the Firebase project to Spark.

## Re-forking (the fork swaps credentials only)

1. New Firebase project (Spark): set RTDB rules + Auth.
2. `sionyx-server`: edit `wrangler.toml` `[vars]` (project DB URL + web API key),
   set its own secrets, `wrangler deploy`.
3. Web: set `VITE_FIREBASE_*` + `VITE_SERVER_URL` (its Worker URL).
4. Kiosk: set its Firebase config + Worker URL + Nedarim creds.

No code changes — only configuration.

---

## Remaining work

- **Saved-card charge server-side** — needs the org's Nedarim **API password**
  captured at registration (today metadata only stores `nedarim_api_valid`, the
  iframe token). Decision required before building.
- **Kiosk:** route print/time **deduction** through the Worker, then tighten RTDB
  rules to deny client writes to `remainingTime`/`printBalance` (ship together so
  printing doesn't break). Shared Critical (C-6) with the original.
- **Auto-update via GitHub Releases** (new kiosk feature) + base64 image uploads.
- **Payment callback cutover** + delete `functions/`.
