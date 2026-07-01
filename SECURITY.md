# Security Policy

SIONYX handles payments and per-user balances, so security reports are taken seriously.

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report privately via GitHub: **Security → Advisories → “Report a vulnerability”**
(private vulnerability reporting is enabled on this repo). Include reproduction steps and
impact. We aim to acknowledge within a few business days.

## Scope & design notes for researchers

- **Money is server-authoritative.** Only the Cloudflare Worker (`sionyx-server`), which
  holds the Firebase service account, may write balances, purchases, and passwords. RTDB
  security rules deny client writes to `remainingTime` / `printBalance` (see
  `database.rules.json` + `tests/rules/`). Reports of a client being able to credit itself
  are high severity.
- **Payment callbacks** are authenticated by a shared secret and verified against the
  stored purchase amount (idempotent). See `docs/CALLBACK-CUTOVER.md`.
- **The kiosk is a locked-down, non-admin Windows device.** Auto-updates are SHA-256
  verified and installed via a SYSTEM scheduled task; the Nedarim gateway password never
  leaves the server.
- Firebase *client* config values (API key, project id, etc.) are public by design and are
  not considered secrets.

## Supported

Only the latest release on `main` is supported.
