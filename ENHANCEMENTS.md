# Enhancements

## Web Admin (`sionyx-web/`)

### ~~ENH-W1: Replace spinners with skeleton loaders~~ DONE
**Files:** `OverviewPage.jsx`, `UsersPage.jsx`, `ComputersPage.jsx`, `PackagesPage.jsx`, `MessagesPage.jsx`  
**Fix applied:** All five pages now use Ant Design `<Skeleton>` components that mirror the page layout. Content placeholders match the real layout structure.

---

### ~~ENH-W2: Localize all English strings to Hebrew~~ DONE
**File:** `src/pages/UsersPage.jsx`  
**Fix applied:** Translated all Modal.confirm titles, content, button labels, and success/error messages to Hebrew.

---

### ~~ENH-W3: Add breadcrumbs navigation~~ DONE
**File:** `src/components/MainLayout.jsx`  
**Fix applied:** Added Ant Design `<Breadcrumb>` below the header showing "ניהול > [current page]".

---

### ENH-W4: Unify card styling across all pages
**Files:** All page components  
**Effort:** ~1 hour  
**Status:** Partially done — Card `bordered={false}` is now consistent. Full `borderRadius` unification across all pages is noted for a future pass.

---

### ~~ENH-W5: Add `confirmLoading` to modal submit buttons~~ DONE
**File:** `src/pages/PackagesPage.jsx`  
**Fix applied:** Added `confirmLoading` to the create/edit modal.

---

### ENH-W6: Add sorting and filtering to tables
**Files:** `UsersPage.jsx` (drawer tables), `ComputersPage.jsx`  
**Effort:** ~2 hours  
**Status:** Pending — tables work but lack sort/filter UI. Good candidate for next sprint.

---

### ~~ENH-W7: Use CSS classes instead of inline hover styles~~ NOTED
**File:** `src/pages/MessagesPage.jsx`  
**Status:** Low priority — current implementation works. CSS refactor noted for future cleanup.

---

### ~~ENH-W8: Show full name in chat user card~~ DONE
**File:** `src/pages/MessagesPage.jsx`  
**Fix applied:** `UserQuickCard` now shows the full `name` variable instead of just `firstName`.

---

## Kiosk App (`sionyx-kiosk-wpf/`)

### ~~ENH-K1: Replace `GetAwaiter().GetResult()` with async/await~~ DONE
**File:** `src/SionyxKiosk/Services/PrintMonitorService.cs`  
**Fix applied:** All three blocking calls refactored to `async/await`.

---

### ENH-K2: Add structured logging context
**Files:** All services  
**Effort:** ~2 hours  
**Status:** Pending — good improvement but not urgent.

---

### ENH-K3: Add integration tests for key flows
**Files:** `tests/SionyxKiosk.Tests/`  
**Effort:** ~4 hours  
**Status:** Pending — recommended for next sprint.

---

### ENH-K4: Implement proper `IAsyncDisposable` shutdown
**Files:** `LocalDatabase`, `FirebaseClient`, `SessionService`  
**Effort:** ~1 hour  
**Status:** Pending — see BUG-K4.

---

## Cloud Functions (`functions/`)

### ~~ENH-F1: Add structured error responses~~ PARTIALLY DONE
**File:** `functions/index.js`  
**Fix applied:** Input validation now returns structured error messages. Full structured response format noted for future improvement.

---

### ~~ENH-F2: Add input type validation to payment callback~~ DONE
**File:** `functions/index.js`  
**Fix applied:** Added type checks for `Amount`, `Param1`, `Param2`.

---

## DevOps / Project

### ~~ENH-D1: Add CI/CD pipeline~~ DONE
**File:** `.github/workflows/ci.yml`  
**Fix applied:** GitHub Actions workflow with two jobs: `web-tests` (Ubuntu, Node 22) and `kiosk-tests` (Windows, .NET 8). Triggers on push/PR to main.

---

### ~~ENH-D2: Add root README.md~~ DONE
**File:** `README.md`  
**Fix applied:** Professional README with architecture overview, quick start, and Makefile commands.

---

### ~~ENH-D3: Add `.env.example` file~~ DONE
**File:** `env.example`  
**Fix applied:** Template with all required environment variables documented.

---

### ~~ENH-D4: Lock `functions/package-lock.json`~~ DONE
**File:** `.gitignore`  
**Fix applied:** Removed the ignore rule for `functions/package-lock.json`. Added exception rules.
