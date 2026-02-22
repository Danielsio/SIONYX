# Bugs

## Web Admin (`sionyx-web/`)

### ~~BUG-W1: `useOrgId` not used consistently~~ FIXED
**File:** `src/pages/MessagesPage.jsx`  
**Severity:** Medium  
**Fix applied:** Replaced `user?.orgId` with `useOrgId()` hook. All `user.orgId` references updated to `orgId`.

---

### ~~BUG-W2: Missing `orgId` in `useEffect` dependencies~~ FIXED
**Files:** `src/pages/MessagesPage.jsx`, `src/pages/ComputersPage.jsx`  
**Severity:** Medium  
**Fix applied:** Added `orgId` to `useEffect` dependency arrays on both pages. Data now reloads when org changes.

---

### ~~BUG-W3: `ErrorBoundary` has unused `handleReset`~~ FIXED
**File:** `src/components/ErrorBoundary.jsx`  
**Severity:** Low  
**Fix applied:** Added a "נסה שוב" (Try Again) button that calls `handleReset` to clear the error state without a full page reload.

---

### ~~BUG-W4: `Card variant='borderless'` may not exist in Ant Design 5~~ FIXED
**Files:** `src/pages/OverviewPage.jsx`, `src/pages/ComputersPage.jsx`  
**Severity:** Low  
**Fix applied:** Replaced `variant='borderless'` with `bordered={false}` on all Card components.

---

### ~~BUG-W5: Footer links are non-functional~~ NOTED
**File:** `src/pages/LandingPage.jsx` (lines 1189–1203)  
**Severity:** Low  
**Status:** Requires actual terms/privacy pages to be created. Noted for future work.

---

### ~~BUG-W6: `html lang="en"` while UI is Hebrew~~ FIXED
**File:** `index.html`  
**Severity:** Low (Accessibility)  
**Fix applied:** Changed to `<html lang="he" dir="rtl">`. Added OG meta tags.

---

### ~~BUG-W7: LoginPage wraps content in duplicate `<App>`~~ FIXED
**File:** `src/pages/LoginPage.jsx`  
**Severity:** Low  
**Fix applied:** Removed the redundant `<App>` wrapper. Content now renders within the parent AntApp context.

---

## Kiosk App (`sionyx-kiosk-wpf/`)

### ~~BUG-K1: `GetVersion()` returns hardcoded `"1.0.0"`~~ FIXED
**File:** `src/SionyxKiosk/App.xaml.cs`  
**Severity:** High  
**Fix applied:** `GetVersion()` now reads from `version.json` at `AppContext.BaseDirectory`. Falls back to `"1.0.0"` if file is missing.

---

### ~~BUG-K2: Null reference risk on `auth.CurrentUser!`~~ FIXED
**File:** `src/SionyxKiosk/App.xaml.cs`  
**Severity:** Medium  
**Fix applied:** Added null check before accessing `CurrentUser`. Throws `InvalidOperationException` with a clear message instead of `NullReferenceException`.

---

### ~~BUG-K3: Blocking UI thread in `PrintMonitorService`~~ FIXED
**File:** `src/SionyxKiosk/Services/PrintMonitorService.cs`  
**Severity:** Medium  
**Fix applied:** Replaced all `GetAwaiter().GetResult()` calls with proper `async/await`. Methods refactored: `LoadPricing` → `LoadPricingAsync`, `GetUserBudget` → `GetUserBudgetAsync`, `DeductBudget` → `DeductBudgetAsync`.

---

### BUG-K4: Missing `IDisposable` cleanup on shutdown
**Files:** `LocalDatabase`, `FirebaseClient`, `SessionService`  
**Severity:** Medium  
**Status:** Pending — requires careful integration testing with the host lifecycle.

---

### BUG-K5: `SseListener.Stop()` blocks synchronously
**File:** `src/SionyxKiosk/Infrastructure/SseListener.cs` (line 63)  
**Severity:** Low  
**Status:** Pending — minor impact, scheduled for next release.

---

## Cloud Functions (`functions/`)

### ~~BUG-F1: `nedarimCallback` lacks input type validation~~ FIXED
**File:** `functions/index.js`  
**Severity:** Medium  
**Fix applied:** Added type validation for `Amount` (must parse as number), `Param1` and `Param2` (must be non-empty strings). Validation failures are logged.
