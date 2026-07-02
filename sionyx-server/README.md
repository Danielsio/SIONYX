# sionyx-server

The SIONYX backend, as a single **Cloudflare Worker**. It replaces all Firebase
Cloud Functions so the project runs entirely on the Firebase **Spark (free)**
plan — **no Blaze, no credit card**. Cloudflare Workers' free plan also requires
no card and has no cold starts (important for Nedarim payment callbacks).

## Why this exists
Cloud Functions require Blaze (a card on file). To stay free, every privileged
operation moves here. This Worker is the **only** holder of the Firebase
service account, so it is the **only** writer of balances, purchases, and
passwords — money is server-authoritative. Clients talk to RTDB directly only
for reads and non-privileged writes (Security Rules deny self-crediting).

## Endpoints
| Method | Path | Replaces | Auth |
|---|---|---|---|
| GET | `/health` | — | none |
| GET | `/version/latest` | — | none |
| POST | `/payments/nedarim-callback` | `nedarimCallback` | gateway signature |
| POST | `/payments/charge-saved-card` | (kiosk-side charge, moved server-side) | user ID token |
| POST | `/auth/reset-request` | `resetUserPassword` (email) | user/none |
| POST | `/auth/yemot` | phone-IVR reset | Yemot webhook |
| POST | `/org/register` | `registerOrganization` | none/captcha |
| POST | `/admin/delete-user` | `deleteUser` | `x-sionyx-secret` |
| cron | daily | `cleanupInactiveUsers` | — |

(Several are scaffolded stubs returning 501; being ported incrementally.)

## Local development
```bash
npm install
cp .dev.vars.example .dev.vars   # fill in real values (gitignored)
npm run dev                      # wrangler dev
npm run check                    # build/dry-run, no deploy
```

## Deploy (one-time auth needed)
```bash
npx wrangler login               # opens a browser; links your Cloudflare account
# set the non-secret vars in wrangler.toml ([vars]) first, then:
npx wrangler secret put FIREBASE_SERVICE_ACCOUNT   # paste the service-account JSON (one line)
npx wrangler secret put ADMIN_SECRET
npx wrangler secret put NEDARIM_MOSAD_ID
npx wrangler secret put NEDARIM_API_PASSWORD
npm run deploy
```
The deployed URL (e.g. `https://sionyx-server.<subdomain>.workers.dev`) goes into
the web/kiosk client config and the Nedarim callback URL.

## Re-forking
A fork only needs to: change `[vars]` in `wrangler.toml` (its Firebase project),
set its own secrets, and deploy. No code changes.
