# Nedarim callback cutover (drop the last Cloud Function)

This is the **final ops step** of the Spark migration. After it, `functions/` can be
deleted and the project uses **no** Firebase Cloud Functions — so the Blaze plan is no
longer required anywhere.

It is intentionally **not automated**: it changes how a live payment gateway reaches the
backend, so it must be staged and verified with a real (small) transaction. Doing it wrong
either drops payment credits or — if the callback secret leaks to a client — lets a user
self-credit without paying.

## Background — the two callback paths

| Path | Who sets the callback | Status |
| --- | --- | --- |
| **Saved-card charge** (`/payments/charge-saved-card`) | the **Worker**, server-side, with the secret | ✅ already on the Worker — nothing to do |
| **Regular iframe payment** (kiosk `PaymentDialog`) | the **client** passes `CallBack` to the Nedarim iframe | ⬅️ this is what we cut over |

The Worker callback (`POST /payments/nedarim-callback`) **fails closed** without
`?secret=<CALLBACK_SECRET>`, then verifies the amount against the stored purchase and is
idempotent. The secret is what stops a user from forging their own "paid" callback, so it
must never sit somewhere an untrusted user can read it.

## Pick how the regular-payment callback is delivered

The kiosk now reads `NedarimCallbackUrl` (registry value / `NEDARIM_CALLBACK_URL`); the
payment dialog uses it as follows:

- **`none`  → _recommended_.** The kiosk sends an **empty** `CallBack`, so the gateway uses
  the callback configured in the **Nedarim mosad dashboard**. Set that dashboard callback to
  `https://<worker-host>/payments/nedarim-callback?secret=<CALLBACK_SECRET>`. The secret then
  lives only at the gateway + the Worker — **never on the kiosk**.
- **a full URL** → the kiosk sends exactly that (e.g. the Worker callback with the secret in
  the query string). Acceptable on a locked-down kiosk (non-admin `SionyxUser`, regedit/cmd
  disabled), and still strictly better than the legacy no-secret function. Simpler than the
  dashboard route if you don't have mosad-settings access.
- **unset** → legacy `https://us-central1-<project>.cloudfunctions.net/nedarimCallback`
  (unchanged behaviour, so existing installs are unaffected until you flip this).

## Staged runbook

1. **Verify the Worker is ready.** `CALLBACK_SECRET` is set as a Worker secret
   (`wrangler secret list`) and `GET /health` returns ok.
2. **Configure the callback** (choose one option above):
   - Option A: set the mosad-dashboard callback at Nedarim, and set `NedarimCallbackUrl=none`
     (via the `NEDARIM_CALLBACK_URL` build/installer secret, or the registry value).
   - Option B: set `NedarimCallbackUrl` to the full Worker callback URL incl. `?secret=…`.
3. **Roll out the new kiosk build to _every_ machine.** Until all kiosks are updated, leave
   `functions/` deployed so older clients still credit.
4. **Test a real transaction** (a minimal package) on an updated kiosk. Confirm the purchase
   flips to `completed` and the balance is credited (the Worker logs `[nedarim] credited`).
   Test a **saved-card** charge too — it already uses the Worker callback.
5. **Delete the function.** Remove the `functions` block from `firebase.json` and delete the
   `functions/` directory, then `firebase deploy` (or simply stop deploying functions). The
   project is now 100% Cloud-Functions-free.

## Rollback

If step 4 fails, revert the callback config (set `NedarimCallbackUrl` back to the legacy
Cloud Function URL or redeploy `functions/`) — no data migration is involved, so it is a
pure configuration flip.
