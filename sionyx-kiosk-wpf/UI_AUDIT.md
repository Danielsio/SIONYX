# SIONYX Kiosk WPF — UI Audit (2026-02-16)

## Screenshots Analyzed

| # | Screen | Key Observations |
|---|--------|------------------|
| 1 | Auth — Login | Clean layout. Gradient panel + form card centered. No issues. |
| 2 | Auth — Register | **Title "ברוכים הבאים" is CUT OFF at the top.** When registration fields appear, the form overflows the fixed-height card and `ClipToBounds` clips the title. |
| 3-4 | Home Page | Stats cards (messages, print balance, time remaining) render correctly. "Start Session" button visible. Sidebar nav items barely readable. |
| 5 | Packages Page | 5 package cards in horizontal row. Looks clean. |
| 6 | Help Page | FAQ + contact section. Copy buttons visible. Renders correctly. |
| 7-8 | **History nav → shows Help** | **Clicking "היסטוריה" in sidebar shows the Help page instead.** The app logged a FATAL crash (`XamlParseException`) — HistoryPage fails to load, so the previous page remains. |

---

## Critical Bugs

### 1. HistoryPage crashes on navigation (FATAL)

**File:** `HistoryPage.xaml` line 8 + `HistoryPage.xaml.cs` line 14

**Cause:** `BoolToVis` resource is defined **twice** — once in XAML (`<Page.Resources>`) and once in code-behind (`Resources["BoolToVis"] = ...` before `InitializeComponent()`). When `InitializeComponent()` runs, it tries to add `BoolToVis` to the already-populated resource dictionary → `ArgumentException: Item has already been added`.

**Crash log:**
```
[FTL] Unhandled UI exception
XamlParseException → ArgumentException: Item has already been added.
Key in dictionary: 'BoolToVis'  Key being added: 'BoolToVis'
```

**Impact:** History page is completely broken. Clicking the nav item triggers two FATAL crashes (user tried twice). Previous page (Help) remains visible, giving the impression that the wrong page loaded.

**Fix:** Remove the duplicate from code-behind. Keep only the XAML declaration.

---

### 2. Register form title clipped

**File:** `AuthWindow.xaml` line 11-13

**Cause:** Auth card has `Width="900" Height="600" ClipToBounds="True"`. The form `StackPanel` has `VerticalAlignment="Center"` and `Margin="48"`. In login mode (2 fields), the content fits in 600px. In register mode (4 fields + extra labels), the total height exceeds the available space. `ClipToBounds` clips the top, hiding "ברוכים הבאים".

**Fix:** Either:
- Remove fixed `Height="600"` → use `MinHeight="600" MaxHeight="720"` 
- Or wrap the form in a `ScrollViewer`
- Or increase card height when register fields are visible

---

### 3. Sidebar nav items almost invisible

**File:** `Theme.xaml` — `SidebarNavButton` style (line 388)

**Cause:** Default `Foreground` is `#FFFFFFAA` (white at 67% opacity) on `SidebarGradient` background (`#111827` → `#0B1220`). This results in very low contrast — items are barely readable until hovered (which sets `Foreground="White"`).

The active (`IsChecked`) state uses `Background="#FFFFFF15"` (white at 8% opacity) which is also nearly invisible.

**Fix:**
- Default foreground → `#FFFFFFCC` (80% opacity) or `#FFFFFFDD` (87%)
- Active background → `#FFFFFF20` (12%) or add a solid primary-tinted bg
- Active state should be visually distinct (currently subtle indicator + bold text is not enough)

---

### 4. NavigateToPage has no error handling

**File:** `MainWindow.xaml.cs` — `NavigateToPage()` line 42-67

**Cause:** `_services.GetService(typeof(HistoryPage))` calls the DI container which constructs the page. If the constructor throws (like the `BoolToVis` crash), the exception propagates up through the `Checked` event handler into the WPF message loop, triggering a FATAL unhandled UI exception.

**Fix:** Wrap the navigation in `try-catch`. Log errors and show a fallback state instead of crashing the entire app.

---

## UI Polish Issues

### 5. Session start perceived freeze

**Observed:** User reports UI freezes when starting a session.

**Log analysis:** Session start at 20:30:25 shows synchronous process cleanup (6 processes killed). The `ProcessCleanupService` kills processes before the session begins. This runs on the UI thread or blocks it briefly. Combined with the FloatingTimer creation and MainWindow minimize, this creates a noticeable stall.

**Fix:** Ensure process cleanup runs async. Also, the FTL crash from HistoryPage (which happened seconds before) may have corrupted the dispatcher state, contributing to perceived freeze.

### 6. Admin exit not firing during active session

**Log evidence:** After session start, three admin exit keypresses were detected by the keyboard hook (20:30:54, 20:30:56, 20:31:00) but the app-level handler never fired. The `InvokeAsync` in the hook callback queues to the UI dispatcher, but after the FATAL crashes (20:30:01), the dispatcher may be in a degraded state.

**Fix:** Add resilient error handling in the hook callback. Also, the admin exit handler should use `BeginInvoke` pattern with error logging.

### 7. Sidebar active state needs stronger visual

The active nav item's `#FFFFFF15` background is almost indistinguishable from the sidebar background. Active items need a more prominent highlight (primary-tinted background, thicker indicator, or a solid left border).

### 8. No visual feedback for navigation loading

Pages like History load data asynchronously. If the page fails to load (as it currently does), the user gets no feedback — the old page just stays.

---

## Fix Priority

| Priority | Issue | Severity |
|----------|-------|----------|
| P0 | HistoryPage `BoolToVis` crash | App-breaking |
| P0 | NavigateToPage error handling | App-breaking |
| P1 | Register form clipping | UX-breaking |
| P1 | Sidebar contrast | UX-breaking |
| P1 | Admin exit reliability | Feature-breaking |
| P2 | Session start smoothness | Polish |
| P2 | Sidebar active state visual | Polish |

---

## Status

- [x] All fixes implemented
- [x] Build succeeds (0 errors, 0 warnings)
- [x] All 793 tests pass
- [x] Committed
