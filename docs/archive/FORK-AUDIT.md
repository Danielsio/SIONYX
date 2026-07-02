# SIONYX Fork — Independent Production-Grade Audit

**Auditor role:** Principal Engineer / Software Architect (independent review)
**Date:** 2026-06-28
**Source of truth:** `Danielsio/SIONYX` (this repo)
**Fork under review:** `maxmax264/SIONYX1`, `maxmax264/sionyx-auth-server`, `maxmax264/sionyx-releases`
**Method:** Both codebases cloned and inspected directly. Every conclusion below cites file/line evidence. Where I could not verify a claim to high confidence, it is marked *Confidence: Medium/Low*.

> **Scope honesty note.** This is a 4-language (JS, Python, C#/WPF, React), multi-repo system. I directly read the security-, money-, and architecture-critical paths (auth server, RTDB rules, payment flow, auto-update, repo hygiene) and diffed the fork against the original. UI/UX and performance sections are assessed at lower confidence because they were sampled, not exhaustively traced. They are labeled accordingly.

---

## 1. Executive Summary

The fork set out to make SIONYX "free to operate." It succeeded at exactly one genuinely good idea — **hosting installer artifacts on GitHub Releases instead of paid storage** — and surrounded it with a large amount of unsafe, redundant, and unmaintainable code.

The headline facts:

1. **The cost goal was not actually met.** The fork keeps the entire Firebase Cloud Functions codebase **byte-for-byte identical** to the original (`functions/index.js` diff = 0 lines). 2nd-gen Cloud Functions require the paid **Blaze** plan. So the "remove paid services" objective failed on its central premise: the paid dependency is still there. The new self-hosted auth server is **additive**, not a replacement.

2. **The new auth server is a parallel, redundant, and insecure system.** It re-implements password reset over a phone-IVR (Yemot Hamashiach) while the original `resetUserPassword` Cloud Function still exists. It authenticates users **solely by caller-ID** with an `endsWith` phone match that is an account-takeover bug, writes **plaintext temporary passwords** into the database, and is deployed on a free tier that cold-starts.

3. **The fork introduced real security regressions in the Firebase rules** that the original does not have — most importantly opening `organizations` read to every authenticated user (a whole-database read cascade) and exposing `adminExitPassword` as a public read.

4. **The auto-update path is a fleet-wide remote-code-execution vector**: kiosks download and install an MSI as SYSTEM with no signature/hash verification, and the endpoint that selects which MSI to push is guarded by a **hardcoded default secret committed to the repo** (`sionyx-admin-2026`).

5. **Repository hygiene is severely degraded**: ~46 `.backup*` files, ~97 throwaway `.py` patch scripts, snapshot copies (`*.v3.4.19`, `*.pre-migration`), a committed `env` file, a nested duplicate of the entire auth server, and a corrupted-name garbage file — all committed.

A prior audit (issue **#9**, a "Blueprint" authored from the fork owner's own account) is **largely correct** and well-written. This audit independently confirms most of it, **refutes one claim** (the gateway `ApiPassword` is *not* shipped to the kiosk; the client-side value is the iframe `ApiValid`, which is client-side by design), and **adds several Critical findings #9 missed** (the org-read cascade, public `adminExitPassword`, the `endsWith` takeover, plaintext password storage, the nested-duplicate broken reset path).

### Verdict

**Do not merge the fork.** **Adopt three ideas** (GitHub-Releases hosting, the auto-update state machine, the saved-card UX), each **re-implemented** to the original's standards. **Keep the project a monorepo.** The fork's repository split is not a deliberate architecture — it is an accident of deployment convenience and produces hidden coupling, not modularity.

### Scorecard (the fork, as-is)

| Dimension | Score | One-line justification |
|---|---|---|
| **Overall repository health** | **3 / 10** | One good idea buried under cruft, redundancy, and security regressions. |
| **Production readiness** | **2 / 10** | Fleet-RCE updater, cold-start auth, plaintext passwords, no CI gates on the new server. |
| **Code quality** | **2.5 / 10** | Script-mangled whitespace, 46 backups, 97 scratch scripts, duplicated server. |
| **Architecture** | **4 / 10** | Good *intentions* (offload storage, decouple auth); poor *execution* (redundant, coupled, split-without-reason). |
| **Maintainability** | **2 / 10** | Vibe-coded via `fix_*.py`; nobody can reason about state across 4 repos + backups. |
| **Security** | **2 / 10** | Multiple Critical: RCE updater, org-read cascade, caller-ID auth bypass, plaintext secrets. |

*For contrast, the original (`Danielsio/SIONYX`) scores roughly: health 6.5, prod-readiness 5.5, code quality 6.5, architecture 6.5, maintainability 6.5, security 5 — it shares the pre-existing self-write-balance flaw (below) but has none of the fork's regressions and far cleaner hygiene.*

---

## 2. Repository Architecture

### Why was the project split into three repos?

The split is **not** a domain-driven decomposition. Reconstructed from the evidence:

- **`sionyx-auth-server`** exists because Railway/Render want a repo with a `package.json` at root to deploy. It was carved out to get a free always-on Node host for the Yemot IVR webhook and the `/latest-version` endpoint.
- **`sionyx-releases`** exists purely as a target for GitHub Releases (it contains only a `README.md`; the MSIs are uploaded as release assets by `upload_release.py`).
- **`SIONYX1`** remains the actual monorepo (web + kiosk + functions + rules) — i.e. the split only *peeled off* two deployment endpoints.

### Does the split make architectural sense? No.

| Symptom | Evidence | Why it's a problem |
|---|---|---|
| **Hidden coupling, not decoupling** | `sionyx-auth-server/index.js` hardcodes `organizations/sionov/...` paths and the same RTDB schema the kiosk/web use. `upload_release.py` lives in `SIONYX1` but calls the auth-server's `/set-latest-version`. | The "services" share a schema and secrets but have no contract, no shared types, no versioning. A rules change in `SIONYX1` silently breaks `sionyx-auth-server`. |
| **Duplication across the split** | `sionyx-auth-server/` contains a **nested second copy** of itself (`sionyx-auth-server/sionyx-auth-server/index.js`) — an *older, broken* variant (uses `identitytoolkit accounts:update` which needs an `idToken` it never supplies). | Two divergent implementations of the same server in one repo; nobody can tell which deploys. |
| **Deployment got harder** | Three repos, three deploy targets (Firebase, Railway/Render, GitHub Releases), inconsistent host references (`railway.json` present but every URL says `onrender.com`). | More moving parts, more places to misconfigure, more cold-start surfaces. |
| **No independent lifecycle** | None of the three can be released, versioned, or rolled back independently in a meaningful way. | The classic test for "should this be its own repo" fails. |

### Recommendation

**Keep a monorepo.** If a separate process host is genuinely needed (it isn't, see §4), use a **monorepo with a `services/auth-server/` package** so schema/types/rules are shared and versioned together. The current split delivers all the costs of microservices (operational sprawl, cold starts, no shared contract) and none of the benefits (independent scaling/lifecycle, team boundaries).

---

## 3. Cost-Reduction Audit (the stated goal)

| Change | What it removed | What replaced it | Verdict |
|---|---|---|---|
| **Installer hosting → GitHub Releases** | Paid Firebase Storage egress for MSI downloads | `upload_release.py` pushes MSI to `maxmax264/sionyx-releases` Releases (free, CDN-backed) | ✅ **Genuinely good idea. Port this.** Reliable, scalable, free. |
| **Password reset → Yemot IVR on Railway/Render** | Nothing — the `resetUserPassword` Cloud Function **still exists** | A free Node host + phone IVR | ❌ **Redundant + insecure.** Adds a second reset path; doesn't remove the first. |
| **Version metadata → `/latest-version` endpoint** | Nothing paid | A free Node endpoint reading RTDB `system/update` | ⚠️ Unnecessary indirection; the client could read RTDB `public/latestRelease` directly (the web app already does). Delete the endpoint. |
| **Cloud Functions** | **Nothing** — kept identical (Blaze still required) | — | ❌ **The core cost goal is unmet.** |

### Reliability / viability of the free replacements

- **Render/Railway free tier cold-starts.** The IVR server sleeps after inactivity; a phone call or update check hitting a cold instance waits ~30–50s. The kiosk updater uses a 10s `HttpClient.Timeout` ([AutoUpdateService.cs:124](sionyx-kiosk-wpf/src/SionyxKiosk/Services/AutoUpdateService.cs#L124)) → cold-start update checks silently fail. For an IVR, a 30s pickup delay is a failed call.
- **Single point of failure.** All auto-update and phone-reset traffic funnels through one free dyno with no health checks, no monitoring, no alerting.
- **Hidden cost:** the engineering time to operate three free services with no observability exceeds the Blaze bill it was trying to avoid (which, with a budget cap, would likely be **$0** at this scale anyway).

**Bottom line:** the only change that actually advances the cost goal *and* is production-sound is **GitHub Releases hosting**. Everything else either doesn't reduce cost (Functions kept) or trades a tiny bill for real reliability/security debt.

---

## 4. Detailed Findings

Severity key: **Critical** = fix before any production use · **High** = fix soon · **Medium** = reliability/maintainability · **Low** = polish.

### CRITICAL

#### C-1 — Fleet-wide RCE via unsigned auto-update + hardcoded push secret
- **Description:** Kiosks fetch `{version, downloadUrl}` from `https://sionyx-auth-server.onrender.com/latest-version`, download the MSI from `downloadUrl`, and install it via a SYSTEM scheduled task. The only integrity check is **Content-Length byte count** — no Authenticode/signature check, no SHA-256, no host allowlist. The endpoint that sets `downloadUrl` (`/set-latest-version`) is guarded by a shared header secret whose **default is hardcoded and committed**: `sionyx-admin-2026`.
- **Evidence:** [AutoUpdateService.cs:601-737](sionyx-kiosk-wpf/src/SionyxKiosk/Services/AutoUpdateService.cs#L601) (download + size-only check, install as SYSTEM); `upload_release.py:90` `admin_secret = os.environ.get("SIONYX_ADMIN_SECRET", "sionyx-admin-2026")`; `sionyx-auth-server/index.js:147-162` (`/set-latest-version`, plain `!==` secret compare).
- **Impact:** Anyone who read the public repo can call `/set-latest-version` with the default secret (if the deployed env var is unset or equals the default) and point every kiosk at a malicious MSI, which auto-installs as SYSTEM. Full fleet compromise.
- **Root cause:** No supply-chain integrity model; secret defaulted to a literal for convenience.
- **Fix:** (a) Authenticode-verify the MSI against a **pinned cert thumbprint** (`WinVerifyTrust`) *and* a signed SHA-256 published in the metadata; (b) validate `downloadUrl` is `https` + GitHub-host allowlisted, reject off-host redirects; (c) remove the hardcoded secret — require the env var, fail closed if missing; (d) prefer reading version metadata from RTDB `public/latestRelease` (rules already `.read:true/.write:false`) and **delete the Render endpoint**.
- **Effort:** ~1 week.

#### C-2 — Firebase rules: `organizations` read opened to every authenticated user (fork regression)
- **Description:** The fork changed the `organizations` node from `".read": false` to `".read": "auth != null"`. In RTDB, a read grant at a parent **cascades to the entire subtree and cannot be narrowed by deeper rules**. Every authenticated user (i.e. every registered kiosk user, in any org) can read the **entire** `organizations` tree: all users' balances, phone numbers, the Nedarim credentials, and `adminExitPassword`.
- **Evidence:** Fork `database.rules.json:32-34` (`"organizations": { ".read": "auth != null"`) vs original `database.rules.json:29-31` (`".read": false`).
- **Impact:** Mass PII + credential + cross-tenant data exposure to any logged-in user. Critical confidentiality breach and multi-tenant isolation failure.
- **Root cause:** Likely a debugging shortcut to make admin/supervisor reads "just work," misunderstanding RTDB cascade semantics.
- **Fix:** Revert to `".read": false` at `organizations`; rely on the per-path read rules already present.
- **Effort:** 15 minutes + rules test.

#### C-3 — Firebase rules: `adminExitPassword` and design nodes are world-readable (fork regression)
- **Description:** Fork rules expose `metadata/settings/adminExitPassword` with `".read": true` (no auth at all), plus `authDesign`/`kioskDesign`/`kioskBackground*` as public reads.
- **Evidence:** Fork `database.rules.json:248-253` (`"adminExitPassword": { ".read": true }`), `:240-245`. Not present in original.
- **Impact:** The password that unlocks the kiosk out of lockdown is readable by anyone on the internet who knows the DB URL (which is in the committed `env`). Kiosk lockdown is fully defeated.
- **Root cause:** Same cascade/ό convenience pattern as C-2.
- **Fix:** Remove public reads; gate exit-password retrieval behind the kiosk's authenticated context or move it out of RTDB entirely.
- **Effort:** 30 minutes.

#### C-4 — Auth server authenticates by caller-ID with an account-takeover `endsWith` match
- **Description:** The IVR identifies the user purely by the incoming phone number, and matches with `userPhone === cleanPhone || userPhone.endsWith(cleanPhone) || cleanPhone.endsWith(userPhone)`. Caller-ID is trivially spoofable on many IVR/SIP setups, and the `endsWith` logic means a partial-number match resets the **wrong** account (e.g. a stored short number is a suffix of many real numbers, or vice-versa).
- **Evidence:** `sionyx-auth-server/index.js:37-52`. Same flaw in the nested copy `:30-39`.
- **Impact:** An attacker can reset another user's password (and thereby take over the Firebase Auth account) by calling from a crafted/related number. The reset **overwrites the real Firebase Auth password** via `admin.auth().updateUser` (`index.js:105`).
- **Root cause:** Treating caller-ID as an authentication factor; fuzzy matching to "be forgiving."
- **Fix:** If keeping IVR at all, require a second factor (a code shown in-app), use **exact** normalized E.164 matching, and never reset without confirming a server-issued challenge. Better: keep the existing `resetUserPassword` Cloud Function (email-based) and delete the IVR path.
- **Effort:** Delete path = trivial; secure redesign ≈ 1 week.

#### C-5 — Plaintext temporary passwords written to the database
- **Description:** On reset, the 6-digit temp password is stored in cleartext at `users/{uid}/passwordReset` *and* `organizations/sionov/passwordResets/{uid}`, with a cosmetic `expiresAt` that nothing enforces (the real Firebase Auth password is already changed).
- **Evidence:** `sionyx-auth-server/index.js:110-119`.
- **Impact:** Combined with C-2 (any user can read `organizations/*`), every reset password is readable by any logged-in user. Plaintext credential storage.
- **Root cause:** Logging/sharing the secret for "debuggability."
- **Fix:** Never persist the password; if a handoff token is needed, store a hash with real server-side expiry enforcement.
- **Effort:** 1–2 hours.

#### C-6 — Any authenticated user can grant themselves unlimited time/print credit (PRE-EXISTING — also in original)
- **Description:** Under `organizations/$orgId/users/$userId`, `.write` allows `auth.uid == $userId`, and `remainingTime` / `printBalance` carry **only `.validate`, no `.write` restriction**, so a user can set their own balances. `printBalance`'s validator doesn't even require `>= 0`. The kiosk's own `DeductBudgetAsync` writes `printBalance` directly, confirming the client-authoritative model.
- **Evidence:** Fork `database.rules.json:43-58`; **identical in original** `database.rules.json:38-56`; client write at [PrintMonitorService.cs:877-906](sionyx-kiosk-wpf/src/SionyxKiosk/Services/PrintMonitorService.cs#L877).
- **Impact:** Any user can REST-write their own `remainingTime`/`printBalance` to any value → unlimited free product. Direct revenue loss.
- **Root cause:** Client-authoritative balance design; balances are user-owned data.
- **Fix:** Make balances server-authoritative: deny user writes to `remainingTime`/`printBalance`; mutate them only from the privileged payment callback / a trusted service. (This is the one Critical the original shares — fixing it benefits both.)
- **Effort:** ~1–2 weeks (requires moving deduction server-side).

#### C-7 — `systemSettings` writable by any authenticated user (fork regression)
- **Description:** Fork rules add `"systemSettings": { ".read": "auth != null", ".write": "auth != null" }`.
- **Evidence:** Fork `database.rules.json:292-295`. Absent in original.
- **Impact:** Any logged-in user can read and overwrite global system settings — integrity/abuse vector depending on what reads them.
- **Fix:** Restrict to admin/supervisor or move to server-only.
- **Effort:** 15 minutes.

### HIGH

#### H-1 — Committed secrets / config (`env`) and project identifiers
- **Description:** The fork commits `env` containing the full Firebase web config for project `pc-sion` (API key, app id, sender id, DB URL). While Firebase *web* API keys are not strict secrets, committing `env` is a hygiene failure, exposes the DB URL used by C-3/C-5, and sets the precedent that produced the broader leakage.
- **Evidence:** `SIONYX1/env` (committed, tracked). The original keeps `.env`/`serviceAccountKey.json` **untracked** (verified via `git ls-files`).
- **Impact:** Easier targeting of the (now over-permissive) database; reputational/secret-rotation burden.
- **Fix:** `git rm --cached env`, add to `.gitignore`, rotate the DB exposure by tightening rules (C-2/C-3), adopt a pre-commit secret scan (gitleaks).
- **Effort:** 1–2 hours.

#### H-2 — Redundant, divergent auth-server duplicate committed
- **Description:** `sionyx-auth-server/` contains a nested `sionyx-auth-server/sionyx-auth-server/` with an **older, broken** server (the `identitytoolkit accounts:update` call requires an `idToken` it never provides → reset would 400). Two implementations, no indication which deploys.
- **Evidence:** `sionyx-auth-server/sionyx-auth-server/index.js:106-115`.
- **Impact:** Severe confusion; risk of deploying the broken one; maintenance hazard.
- **Fix:** Delete the nested copy; keep one server with one entrypoint.
- **Effort:** 15 minutes.

#### H-3 — Render free-tier cold start vs 10s update timeout / IVR latency
- **Description:** See §3. Cold starts cause silent update-check failures and failed/awkward phone calls.
- **Evidence:** [AutoUpdateService.cs:124](sionyx-kiosk-wpf/src/SionyxKiosk/Services/AutoUpdateService.cs#L124); `railway.json` vs hardcoded `onrender.com` URLs.
- **Fix:** Remove the always-on dependency (read metadata from RTDB); if a server is required, add health pings and a paid-but-capped or keep-warm strategy.
- **Effort:** 0.5–1 week (folds into C-1).

#### H-4 — No CI / tests / lint on `sionyx-auth-server`
- **Description:** The server holds admin credentials and can change any user's password, yet has no tests, no lint, no CI, and only `console.log` logging.
- **Evidence:** `sionyx-auth-server/package.json` has only `"start"`; no test/CI files in the repo.
- **Fix:** Add tests for `findUserByPhone`, the `/set-latest-version` auth, and reset flow; add CI; structured logging.
- **Effort:** 2–3 days.

#### H-5 — Save-card defaults to ON (consent regression)
- **Description:** The commit `checkpoint: ... CVV removal, default-on` and the iframe flow indicate saved-card ("keva") is enabled by default rather than explicit opt-in. Storing a reusable payment token without affirmative consent is a consumer-consent problem.
- **Evidence:** `sionyx-kiosk-wpf/.../Assets/templates/payment.html:587-590` (save-card → `CreateToken`); commit message on fork `HEAD`. *Confidence: Medium* (checkbox default attribute not exhaustively traced).
- **Fix:** Save-card checkbox unchecked by default; explicit opt-in copy.
- **Effort:** 1–2 hours.

### MEDIUM

- **M-1 — Repo cruft (~46 `.backup*`, `*.v3.4.19`, `*.pre-migration`, 97 `.py` scratch scripts, garbage file `ersuserDesktoppc 1SIONYX-cleansionyx-kiosk-wpf"`).** Evidence: Glob of `**/*.backup*`; root listing of `SIONYX1`. Impact: nobody can distinguish live code from dead copies; grep noise; review impossible. Fix: delete all; add `.gitignore` rules; enforce in CI. Effort: 0.5 day.
- **M-2 — Script-mangled source formatting.** `AutoUpdateService.cs` has double/triple blank lines throughout from `add_logs.py`-style edits. Impact: diffs unreadable, merge pain. Fix: run formatter (`dotnet format`, Prettier), ban script edits. Effort: 0.5 day.
- **M-3 — `console.log` of secrets in auth server.** `index.js:103` logs the generated temp password; `:22` logs every request URL. Impact: secrets in host logs. Fix: remove; use leveled logging. Effort: 1 hour.
- **M-4 — Hardcoded tenant `sionov`.** Auth server hardcodes `organizations/sionov/...`. Impact: not multi-tenant; breaks for any other org. Fix: parametrize. Effort: 2–3 hours.
- **M-5 — `.backup` files contain real config patterns** (`OrganizationMetadataService.cs.backup1` shows Nedarim decode logic). Folds into M-1 but worth a secret scan before deletion.

### LOW
- **L-1 — Inconsistent deploy descriptors** (`railway.json` but `onrender.com` URLs). Pick one; document it.
- **L-2 — IVR text/audio duplication** (two TTS/audio strategies across the two server copies). Resolve with H-2.
- **L-3 — `.firebaserc`/project rename to `pc-sion`** undocumented; onboarding will break. Document.
- **L-4 — Magic numbers** (6-digit vs 4-digit temp password differ between the two server copies). Standardize.

---

## 5. Verification of the Prior Audit (Issue #9)

Issue #9 ("Blueprint…", authored by `maxmax264`) is a high-quality, mostly-correct review. Independent verdicts:

| #9 claim | My verdict | Evidence |
|---|---|---|
| Kiosk lockdown is user-mode (keyboard hook + process-blacklist killer), escapable | **Confirmed (mechanism)** | `KeyboardRestrictionService.cs`, `ProcessRestrictionService.cs`, `KioskPolicyService.cs` exist; matches description. *Effectiveness of bypass not exploit-tested — Confidence: Medium.* |
| Auto-update installs server-controlled MSI as SYSTEM with only a byte-count check | **Confirmed** | C-1 evidence. |
| Payments credit balances client-side / users can write balances | **Confirmed (balances)** | C-6: rules + `DeductBudgetAsync`. |
| Gateway **`ApiPassword`** is shipped to the kiosk | **Refuted / False Positive** | The client value is **`ApiValid`** (the Nedarim *iframe* token, client-side by design), not the server `ApiPassword`. `payment.html:589-595` posts `ApiValid` into the hosted iframe. No `ApiPassword` found in kiosk/web source. The *real* issue is C-6 (self-writable balances), not a leaked charge credential. |
| Save-card should be opt-in; misleading CVV copy | **Confirmed (default-on)** | H-5. CVV is correctly hidden for tokenized flow (`CVV=Hide`), so "no CVV collected" is accurate, not misleading — partial. |
| Messaging page never subscribes (dead real-time) | **Not independently verified** | Data layer present; subscription not traced this pass. *Confidence: Low.* |
| Logging to RTDB is a footgun; keep Serilog local | **Confirmed (direction)** | Kiosk does PUT update logs to RTDB (`AutoUpdateService.LogUpdateToFirebase`). |
| Secrets in git + ~50% repo cruft | **Confirmed** | H-1, M-1. |

### Issues #9 **missed** (added by this audit)
- **C-2** `organizations` read cascade (whole-DB exposure) — *not mentioned*.
- **C-3** public `adminExitPassword` read — *not mentioned*.
- **C-4** caller-ID `endsWith` account-takeover — *not called out specifically*.
- **C-5** plaintext password persistence — *not mentioned*.
- **C-7** `systemSettings` open write — *not mentioned*.
- **H-2** nested duplicate broken server — *not mentioned*.

Net: this audit raises confidence on #9's correct items, removes one false positive, and adds five Critical/High findings.

---

## 6. Improvement Plan (phased roadmap)

**Phase 1 — Critical security (block production):**
C-1 signed/verified updater + kill hardcoded secret · C-2/C-3/C-7 revert rule regressions · C-4/C-5 delete or secure the IVR reset & stop storing plaintext · C-6 server-authoritative balances (shared with original). *~2–3 weeks.*

**Phase 2 — Architecture consolidation:**
Re-monorepo · delete `sionyx-auth-server` duplicate (H-2) · remove always-on dependency, read `public/latestRelease` from RTDB (H-3) · single deploy story. *~1–2 weeks.*

**Phase 3 — Performance / reliability:**
Replace whole-node RTDB reads with indexed queries · add health checks/observability if any server remains · updater retry/timeout tuning. *~1 week.*

**Phase 4 — Developer experience / hygiene:**
M-1 purge cruft + `.gitignore` + gitleaks pre-commit · M-2 formatters · H-4 CI/tests/lint for any server · Conventional Commits (replace `checkpoint:`). *~1 week.*

**Phase 5 — Future enhancements:**
OS-enforced kiosk lockdown (Assigned Access / Shell Launcher v2 + watchdog) · centralized $0 log viewer (self-host Seq/Loki) · gateway abstraction so Nedarim isn't hardcoded. *~2–4 weeks.*

---

## 7. GitHub Issue Drafts

> These are **drafts only** — nothing is posted. Tell me where to file them (your repo vs the fork) and I'll create them.

**Title:** `[CRITICAL] Auto-update is a fleet-wide RCE: unsigned MSI + hardcoded push secret`
**Labels:** `security`, `critical`, `kiosk`, `supply-chain`
**Problem:** Kiosks install server-supplied MSIs as SYSTEM with only a byte-count check; `/set-latest-version` defaults to committed secret `sionyx-admin-2026`.
**Background:** Update URL fetched from `onrender.com/latest-version`; installed via SYSTEM scheduled task.
**Technical details:** `AutoUpdateService.cs:601-737`; `upload_release.py:90`; `sionyx-auth-server/index.js:147-162`.
**Acceptance criteria:** Updater rejects unsigned/off-allowlist MSI; verifies pinned-thumbprint Authenticode + signed SHA-256; no hardcoded secret (fail-closed); metadata read from RTDB `public/latestRelease`.
**Priority:** P0 · **Dependencies:** none.

**Title:** `[CRITICAL] RTDB rules expose all organizations to any authenticated user`
**Labels:** `security`, `critical`, `firebase-rules`
**Problem:** `organizations` `.read` was changed from `false` to `auth != null`; RTDB cascades reads to the whole subtree.
**Technical details:** fork `database.rules.json:32-34` vs original `:29-31`.
**Acceptance criteria:** Direct authed REST read of another org's `users` is denied; rules tests cover it.
**Priority:** P0.

**Title:** `[CRITICAL] adminExitPassword and systemSettings are world-readable / world-writable`
**Labels:** `security`, `critical`, `firebase-rules`
**Technical details:** `database.rules.json:248-253` (`adminExitPassword .read:true`), `:292-295` (`systemSettings .read/.write: auth!=null`).
**Acceptance criteria:** Exit password not publicly readable; systemSettings writes restricted to admin/server.
**Priority:** P0.

**Title:** `[CRITICAL] IVR password reset: caller-ID auth + endsWith takeover + plaintext storage`
**Labels:** `security`, `critical`, `auth-server`
**Technical details:** `sionyx-auth-server/index.js:37-52, 102-119`.
**Acceptance criteria:** No reset on fuzzy/spoofable caller-ID alone; no plaintext password persisted; second factor required, or path removed in favor of `resetUserPassword` function.
**Priority:** P0.

**Title:** `[CRITICAL] Users can self-write remainingTime/printBalance (revenue bypass)`
**Labels:** `security`, `critical`, `payments`, `affects-original`
**Technical details:** rules `:43-58` (fork) / `:38-56` (original); `PrintMonitorService.cs:877-906`.
**Acceptance criteria:** Authed REST write to own `remainingTime`/`printBalance` denied; balances mutate only via privileged path.
**Priority:** P0 · **Note:** also fixes the original.

**Title:** `[HIGH] Remove committed env + nested duplicate auth server; add secret scan`
**Labels:** `security`, `high`, `hygiene` · **Technical details:** `SIONYX1/env`; `sionyx-auth-server/sionyx-auth-server/`.

**Title:** `[HIGH] Auto-update server: remove always-on dependency / handle cold starts`
**Labels:** `reliability`, `high` · **Technical details:** `AutoUpdateService.cs:124` 10s timeout vs Render cold start.

**Title:** `[MEDIUM] Purge repo cruft (46 backups, 97 .py scripts) and enforce formatting/CI`
**Labels:** `tech-debt`, `medium` · plus **Save-card opt-in (HIGH)** and **auth-server CI/tests (HIGH)** as separate issues.

---

## 8. Final Recommendation

**Adopt from the fork (re-implemented to spec, not merged):**
1. **GitHub Releases for installer hosting** — the one unambiguous win.
2. **The auto-update state machine** (registry-poll install confirmation, install cooldown, retry-on-next-tick, unique temp filenames) — the *control flow* is decent; bolt on signature verification and drop the Render endpoint.
3. **Saved-card ("keva") UX** via the Nedarim hosted iframe (`CreateToken`) — keep the iframe approach (PAN never touches us), but make consent opt-in and keep crediting server-authoritative.

**Reject from the fork:**
- The self-hosted IVR auth server (redundant + C-4/C-5).
- Every RTDB rule loosening (C-2/C-3/C-7).
- The repo split, the nested duplicate, the `.py`/`.backup` workflow, committed `env`.

**Redesign (in the original too):**
- **Balances must be server-authoritative** (C-6) — the single most important fix that benefits both codebases.
- Kiosk lockdown should move to **OS-enforced Assigned Access / Shell Launcher v2 + watchdog** rather than a user-mode hook.

**Monorepo vs split:** **Stay a monorepo.** If a process host is ever truly needed, make it a package *inside* the monorepo so rules/schema/types stay versioned together.

**Ideal architecture, from scratch ($0-capable, production-grade):**
- One monorepo: `apps/web`, `apps/kiosk`, `services/payment-callback`, `packages/shared-schema`, `firebase/` (rules+config).
- **Server-authoritative money:** a single charge/credit endpoint (Blaze function with a hard budget cap, *or* a tiny self-hosted Node+SQLite service) holding the Nedarim `ApiPassword`; clients never write balances; RTDB rules deny user writes to balance fields.
- **Updates:** GitHub Releases + signed MSI verified against a pinned thumbprint + SHA-256 in RTDB `public/latestRelease`; no always-on server.
- **Kiosk lockdown:** Assigned Access/Shell Launcher v2 + AppLocker/WDAC allowlist + watchdog service; passwordless low-priv kiosk account.
- **Secrets:** CI secrets + `firebase functions:secrets`; gitleaks pre-commit + CI gate; nothing in git, ever.
- **Observability:** Serilog rolling local files; optional self-hosted Seq/Loki for $0 central viewing; never stream app logs to RTDB.

---

*End of audit. Evidence for every claim is cited inline; items I could not verify to high confidence are labeled. Happy to (a) post any subset of the issue drafts to a chosen repo, (b) produce a matching remediation PR plan for the original, or (c) deep-dive any single finding with a written exploit/repro.*
