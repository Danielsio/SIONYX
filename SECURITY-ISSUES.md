# Security Issues

## CRITICAL

### ~~SEC-1: Payment callback endpoint has no authentication~~ MITIGATED
**File:** `functions/index.js` — `nedarimCallback`  
**Severity:** Critical  
**Fix applied:** Added configurable shared secret validation. If `CALLBACK_SECRET` is set (via env or Firebase config), the callback checks for a matching `secret` query parameter or `x-callback-secret` header. Returns 403 if invalid.  
**Remaining:** Set up the actual secret in production and configure Nedarim Plus to send it. Consider IP allowlisting as an additional layer.

---

### ~~SEC-2: "Encryption" is just base64 encoding~~ FIXED
**File:** `functions/index.js` — `encryptData`  
**Severity:** High  
**Fix applied:** Replaced base64 with AES-256-CBC encryption using Node.js `crypto`. Key read from `ENCRYPTION_KEY` env variable or Firebase config. Added `decryptData` function. Falls back to base64 with warning if no key is configured (backward compatible).  
**Action needed:** Set `ENCRYPTION_KEY` in production environment.

---

## HIGH

### SEC-3: Firebase API key and admin password hardcoded in installer script
**File:** `sionyx-kiosk-wpf/installer.nsi` (lines 98–111)  
**Severity:** High  
**Status:** Pending — requires changes to the build pipeline. API key exposure is acceptable for client Firebase apps, but the admin password should be injected at build time.

---

### SEC-4: Default admin exit password is weak
**File:** `src/SionyxKiosk/Infrastructure/AppConstants.cs` (line 14)  
**Severity:** High  
**Status:** Pending — requires business decision on whether to remove the default or enforce strong passwords.

---

### SEC-5: Refresh token stored unencrypted
**File:** `src/SionyxKiosk/Infrastructure/LocalDatabase.cs`  
**Severity:** Medium  
**Status:** Pending — DPAPI integration requires testing on target kiosk hardware.

---

### ~~SEC-6: Full raw payment response stored in database~~ FIXED
**File:** `functions/index.js`  
**Severity:** Medium  
**Fix applied:** `rawResponse` now only stores sanitized fields: `TransactionId`, `Status`, `Amount`, `CreditCardNumber` (already masked), `Param1`, `Param2`. Other potentially sensitive fields are excluded.

---

## LOW

### SEC-7: No rate limiting on Cloud Functions
**Files:** `functions/index.js` — all three functions  
**Severity:** Low  
**Status:** Pending — consider Firebase App Check or custom rate limiting for a future release.

---

### ~~SEC-8: `.gitignore` blocks `.env.example`~~ FIXED
**File:** `.gitignore`  
**Severity:** Low  
**Fix applied:** Added `!env.example` exception. Created `env.example` template with all required environment variables documented.
