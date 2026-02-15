# SIONYX Kiosk - Migration from PyQt6 to WPF (.NET 8)

## Technology Decision

### WPF (.NET 8) over WinUI 3 - Rationale

| Criteria | WPF (.NET 8) | WinUI 3 |
|----------|-------------|---------|
| Maturity | 18+ years, rock-solid | 3 years, still maturing |
| Installer | NSIS/MSI (we already use NSIS) | Requires MSIX (complex) |
| Kiosk track record | Proven in POS, ATMs, kiosks worldwide | Very few kiosk deployments |
| UI libraries | MaterialDesignInXAML, HandyControl, MahApps | Limited third-party |
| WebView2 | Full support | Full support |
| Win32 API (P/Invoke) | Trivial, first-class | Same |
| Single-file publish | Yes (.NET 8) | Complicated |
| Community/docs | Massive | Growing but small |
| RTL support | Full XAML FlowDirection="RightToLeft" | Full |
| Animation | Storyboards, VisualStateManager | Composition APIs |
| MVVM tooling | CommunityToolkit.Mvvm (mature) | Same |

**Winner: WPF (.NET 8) with MaterialDesignInXAML for modern UI**

---

## Architecture

### Pattern: MVVM (Model-View-ViewModel)

```
sionyx-kiosk-wpf/
├── SionyxKiosk.sln                  # Solution file
├── src/
│   └── SionyxKiosk/
│       ├── SionyxKiosk.csproj       # Project file
│       ├── App.xaml / App.xaml.cs    # App entry, DI container, global resources
│       ├── Models/                   # Data models (User, Package, Session, etc.)
│       ├── ViewModels/              # MVVM ViewModels
│       ├── Views/                   # XAML views (windows, pages, dialogs)
│       │   ├── Windows/            # AuthWindow, MainWindow
│       │   ├── Pages/              # HomePage, PackagesPage, HistoryPage, HelpPage
│       │   ├── Dialogs/            # PaymentDialog, AlertModal, MessageModal, ConfirmDialog
│       │   └── Controls/           # FloatingTimer, StatCard, ActionButton, etc.
│       ├── Services/               # Business logic (auth, session, print, etc.)
│       ├── Infrastructure/         # Firebase client, local DB, registry, device info
│       ├── Converters/             # XAML value converters
│       ├── Themes/                 # Resource dictionaries, styles, colors
│       ├── Assets/                 # Icons, images, fonts
│       └── Helpers/                # Extensions, utilities
├── tests/
│   └── SionyxKiosk.Tests/
│       ├── SionyxKiosk.Tests.csproj
│       ├── ViewModels/
│       ├── Services/
│       └── Infrastructure/
├── installer/
│   └── installer.nsi               # NSIS installer script
└── MIGRATION.md                     # This file
```

### Key NuGet Packages

| Package | Purpose | Replaces |
|---------|---------|----------|
| `CommunityToolkit.Mvvm` | MVVM framework (ObservableObject, RelayCommand) | PyQt signals/slots |
| `MaterialDesignThemes` | Modern Material Design UI | Custom QSS styling |
| `MaterialDesignColors` | Color palette | Custom color constants |
| `Microsoft.Extensions.DependencyInjection` | DI container | Manual wiring |
| `Microsoft.Extensions.Hosting` | App host lifecycle | Manual setup |
| `FirebaseDatabase.net` | Firebase Realtime DB | `firebase_client.py` |
| `FirebaseAuthentication.net` | Firebase Auth REST | `firebase_client.py` |
| `Microsoft.Web.WebView2` | Embedded browser (payment) | PyQt6-WebEngine |
| `Serilog` + `Serilog.Sinks.File` | Structured logging | `logger.py` |
| `System.Management` | WMI (optional) | N/A |
| `xunit` + `Moq` + `FluentAssertions` | Testing | pytest + pytest-mock |
| `Velopack` | Auto-update & installer | NSIS + manual build |

---

## Component Migration Map

### Phase 1: Foundation (Infrastructure + Core Services)

These have no UI dependency and can be built and tested first.

| # | Python Component | C# Equivalent | Effort | Notes |
|---|-----------------|---------------|--------|-------|
| 1.1 | `utils/firebase_config.py` | `Infrastructure/FirebaseConfig.cs` | S | Registry + .env config loading |
| 1.2 | `utils/registry_config.py` | `Infrastructure/RegistryConfig.cs` | S | `Microsoft.Win32.Registry` |
| 1.3 | `utils/device_info.py` | `Infrastructure/DeviceInfo.cs` | S | `Environment.MachineName`, `NetworkInterface` |
| 1.4 | `utils/const.py` | `Infrastructure/AppConstants.cs` | S | Static constants |
| 1.5 | `utils/error_translations.py` | `Infrastructure/ErrorTranslations.cs` | S | Dictionary mapping |
| 1.6 | `utils/purchase_constants.py` | `Models/PurchaseStatus.cs` | S | Enum + extension methods |
| 1.7 | `utils/logger.py` | `Infrastructure/Logging/` | S | Serilog setup (much simpler) |
| 1.8 | `database/local_db.py` | `Infrastructure/LocalDatabase.cs` | S | SQLite or LiteDB |
| 1.9 | `services/firebase_client.py` | `Infrastructure/FirebaseClient.cs` | M | `FirebaseDatabase.net` + `FirebaseAuthentication.net` + SSE |
| 1.10 | `services/base_service.py` | `Services/BaseService.cs` | S | Abstract base with error handling |
| 1.11 | `services/decorators.py` | N/A (use DI + middleware) | S | Replaced by DI patterns |

**Phase 1 Total: ~3-4 days**

---

### Phase 2: Business Services (No UI)

| # | Python Component | C# Equivalent | Effort | Notes |
|---|-----------------|---------------|--------|-------|
| 2.1 | `services/auth_service.py` | `Services/AuthService.cs` | M | Firebase REST auth, token refresh, single-session |
| 2.2 | `services/computer_service.py` | `Services/ComputerService.cs` | S | Register/associate computer |
| 2.3 | `services/organization_metadata_service.py` | `Services/OrganizationService.cs` | S | Org metadata, print pricing, operating hours |
| 2.4 | `services/package_service.py` | `Services/PackageService.cs` | S | CRUD packages |
| 2.5 | `services/purchase_service.py` | `Services/PurchaseService.cs` | S | Pending purchases, history |
| 2.6 | `services/chat_service.py` | `Services/ChatService.cs` | M | SSE streaming, unread messages, cache |
| 2.7 | `services/operating_hours_service.py` | `Services/OperatingHoursService.cs` | M | DispatcherTimer, signals → events |
| 2.8 | `services/session_service.py` | `Services/SessionService.cs` | L | Full session lifecycle, countdown, sync, cleanup orchestration |
| 2.9 | `services/session_manager.py` | (Merge into SessionService) | - | Simplify: one session service |
| 2.10 | `services/browser_cleanup_service.py` | `Services/BrowserCleanupService.cs` | S | `Process.Start` with `CreateNoWindow` |
| 2.11 | `services/process_cleanup_service.py` | `Services/ProcessCleanupService.cs` | S | `Process.GetProcesses()`, kill targets |
| 2.12 | `services/process_restriction_service.py` | `Services/ProcessRestrictionService.cs` | M | DispatcherTimer, process monitoring |

**Phase 2 Total: ~4-5 days**

---

### Phase 3: Windows System Services (P/Invoke)

| # | Python Component | C# Equivalent | Effort | Notes |
|---|-----------------|---------------|--------|-------|
| 3.1 | `services/print_monitor_service.py` | `Services/PrintMonitorService.cs` | L | `System.Printing` + P/Invoke for `FindFirstPrinterChangeNotification`. C# has **much** better printing APIs than Python. |
| 3.2 | `services/keyboard_restriction_service.py` | `Services/KeyboardRestrictionService.cs` | M | Low-level keyboard hook via `SetWindowsHookEx` P/Invoke. Well-documented in C#. |
| 3.3 | `services/global_hotkey_service.py` | `Services/GlobalHotkeyService.cs` | S | `RegisterHotKey` Win32 API (simpler than Python `keyboard` library) |

**Phase 3 Total: ~3-4 days**

---

### Phase 4: Theme & Design System

| # | Python Component | C# Equivalent | Effort | Notes |
|---|-----------------|---------------|--------|-------|
| 4.1 | `constants/ui_constants.py` (FROST) | `Themes/Colors.xaml` | M | ResourceDictionary with colors, brushes, gradients |
| 4.2 | `styles/theme.py` | `Themes/Theme.xaml` | M | Global implicit styles for all controls |
| 4.3 | `styles/tokens.py` | `Themes/Typography.xaml` | S | Font sizes, weights as StaticResources |
| 4.4 | N/A | `Themes/Animations.xaml` | M | Reusable Storyboard resources |
| 4.5 | All inline QSS | MaterialDesign + custom styles | M | Massive improvement: XAML styles are declarative, reusable, themeable |

**Phase 4 Total: ~2-3 days**

---

### Phase 5: Reusable Controls (UserControls)

| # | Python Component | C# Equivalent | Effort | Notes |
|---|-----------------|---------------|--------|-------|
| 5.1 | `FrostCard` | `Controls/FrostCard.xaml` | S | Border with shadow, corner radius |
| 5.2 | `StatCard` | `Controls/StatCard.xaml` | S | Icon + title + value card |
| 5.3 | `ActionButton` | `Controls/ActionButton.xaml` | S | Styled button (primary/secondary/danger/ghost) with hover animations |
| 5.4 | `PageHeader` | `Controls/PageHeader.xaml` | S | Gradient title bar |
| 5.5 | `LoadingSpinner` | `Controls/LoadingSpinner.xaml` | S | ProgressRing or custom Storyboard animation |
| 5.6 | `EmptyState` | `Controls/EmptyState.xaml` | S | Icon + message placeholder |
| 5.7 | `StatusBadge` | `Controls/StatusBadge.xaml` | S | Colored label |
| 5.8 | `FloatingTimer` | `Controls/FloatingTimer.xaml` | M | Topmost, draggable, warning states, return button |
| 5.9 | `LoadingOverlay` | `Controls/LoadingOverlay.xaml` | S | Full-screen semi-transparent with spinner |
| 5.10 | `MessageCard` | `Controls/MessageCard.xaml` | S | Message display with hover effect |
| 5.11 | `PurchaseCard` | `Controls/PurchaseCard.xaml` | S | Purchase history item |

**Phase 5 Total: ~2-3 days**

---

### Phase 6: Views (XAML Pages + ViewModels)

| # | Python Component | C# Equivalent | Effort | Notes |
|---|-----------------|---------------|--------|-------|
| 6.1 | `auth_window.py` | `Views/Windows/AuthWindow.xaml` + `ViewModels/AuthViewModel.cs` | L | Sliding panels with Storyboard animations. Will look **significantly** better in XAML. |
| 6.2 | `main_window.py` | `Views/Windows/MainWindow.xaml` + `ViewModels/MainViewModel.cs` | L | Sidebar navigation + Frame content. NavigationService pattern. |
| 6.3 | `pages/home_page.py` | `Views/Pages/HomePage.xaml` + `ViewModels/HomeViewModel.cs` | M | Stats grid, session controls, messages badge |
| 6.4 | `pages/packages_page.py` | `Views/Pages/PackagesPage.xaml` + `ViewModels/PackagesViewModel.cs` | M | Scrollable grid, purchase flow |
| 6.5 | `pages/history_page.py` | `Views/Pages/HistoryPage.xaml` + `ViewModels/HistoryViewModel.cs` | M | Filter/search, sorted list |
| 6.6 | `pages/help_page.py` | `Views/Pages/HelpPage.xaml` + `ViewModels/HelpViewModel.cs` | S | FAQ accordion, contact cards |
| 6.7 | `payment_dialog.py` | `Views/Dialogs/PaymentDialog.xaml` + `ViewModels/PaymentViewModel.cs` | M | WebView2 (replaces QWebEngineView). Better JS interop via `CoreWebView2.PostWebMessageAsString`. |
| 6.8 | `modern_dialogs.py` | `Views/Dialogs/ModernDialog.xaml` (+ MessageBox, Confirm, Toast) | M | Custom Window with fade animation |
| 6.9 | `alert_modal.py` | `Views/Dialogs/AlertDialog.xaml` | S | Type-based gradient header |
| 6.10 | `message_modal.py` | `Views/Dialogs/MessageDialog.xaml` + `ViewModels/MessageViewModel.cs` | M | Read/next/finish flow |
| 6.11 | `force_logout_listener.py` | `Services/ForceLogoutService.cs` | S | SSE listener, raises event |
| 6.12 | `web/local_server.py` | `Infrastructure/LocalFileServer.cs` | S | `HttpListener` (built-in .NET) |

**Phase 6 Total: ~6-8 days**

---

### Phase 7: App Shell & Integration

| # | Component | Effort | Notes |
|---|-----------|--------|-------|
| 7.1 | `App.xaml.cs` - DI container, startup, global exception handling | M | `Microsoft.Extensions.Hosting` |
| 7.2 | Navigation service (sidebar → pages) | M | Frame-based navigation with transition animations |
| 7.3 | Kiosk mode (fullscreen, keyboard lock, process restriction) | M | Wire up system services |
| 7.4 | CLI args (`--kiosk`, `--verbose`) | S | `Environment.GetCommandLineArgs()` |
| 7.5 | Single-instance enforcement | S | `Mutex` (built-in) |
| 7.6 | System tray icon | S | `NotifyIcon` |
| 7.7 | Crash handling + logging | S | `AppDomain.UnhandledException` + Serilog |

**Phase 7 Total: ~2-3 days**

---

### Phase 8: Build & Distribution

| # | Component | Effort | Notes |
|---|-----------|--------|-------|
| 8.1 | `.csproj` publish profile (single-file, trimmed, AOT) | M | `dotnet publish -c Release -r win-x64 --self-contained` |
| 8.2 | NSIS installer script | M | Adapt existing `installer.nsi` for .NET output |
| 8.3 | `build.py` equivalent (or PowerShell script) | M | Version bump, build, upload to Firebase Storage |
| 8.4 | Firebase Storage upload | S | Reuse existing `build.py` logic or port to C# |
| 8.5 | Auto-update (optional) | L | Velopack or Squirrel.Windows |

**Phase 8 Total: ~2-3 days**

---

### Phase 9: Testing

| # | Component | Effort | Notes |
|---|-----------|--------|-------|
| 9.1 | Unit tests for all services | L | xUnit + Moq + FluentAssertions |
| 9.2 | Unit tests for ViewModels | M | Test commands, property changes, validation |
| 9.3 | Integration tests | M | Test full flows with mocked Firebase |
| 9.4 | UI automation tests (optional) | L | Appium or FlaUI for kiosk scenarios |

**Phase 9 Total: ~4-5 days (parallel with other phases)**

---

## Migration Summary

| Phase | Description | Effort | Dependencies |
|-------|-------------|--------|-------------|
| 1 | Foundation (infra, config, Firebase client) | 3-4 days | None |
| 2 | Business services (auth, session, chat, etc.) | 4-5 days | Phase 1 |
| 3 | Windows system services (print, keyboard, hotkey) | 3-4 days | Phase 1 |
| 4 | Theme & design system | 2-3 days | None (parallel) |
| 5 | Reusable controls | 2-3 days | Phase 4 |
| 6 | Views + ViewModels | 6-8 days | Phases 2, 3, 5 |
| 7 | App shell & integration | 2-3 days | Phase 6 |
| 8 | Build & distribution | 2-3 days | Phase 7 |
| 9 | Testing | 4-5 days | Parallel |
| **Total** | | **~28-38 days** | |

---

## What Gets Better in WPF

| Area | PyQt6 (Current) | WPF (.NET 8) |
|------|-----------------|-------------|
| **UI Styling** | QSS (CSS-like, limited) | XAML Styles + Templates (full control over every pixel) |
| **Animations** | QPropertyAnimation (manual, code-heavy) | Storyboards in XAML (declarative, visual preview) |
| **Data Binding** | Manual signal/slot wiring | `{Binding}` with automatic change notification |
| **Component reuse** | Python inheritance (fragile) | UserControl + DataTemplate (composable) |
| **Theme support** | Manual QSS string building | ResourceDictionary merging (swap entire themes) |
| **Material Design** | DIY from scratch | MaterialDesignInXAML (complete library) |
| **Print APIs** | `win32print` via `pywin32` + `ctypes` | `System.Printing` (managed, type-safe) + P/Invoke |
| **Keyboard hooks** | `ctypes` + `keyboard` lib | `SetWindowsHookEx` P/Invoke (well-documented) |
| **WebView** | QWebEngineView (bundles Chromium, ~100MB) | WebView2 (uses system Edge, ~2MB) |
| **Installer size** | ~80-150MB (Python + Qt + Chromium) | ~30-50MB (trimmed .NET + WebView2 bootstrapper) |
| **Startup time** | 3-5 seconds | <1 second (AOT compiled) |
| **Memory usage** | ~150-250MB | ~50-100MB |
| **Testing** | pytest-qt (works but hacky for UI) | xUnit + Moq (clean MVVM testability) |
| **Async/await** | QThread + signals (complex) | Native `async/await` (simple) |
| **RTL layout** | Manual `setLayoutDirection` per widget | `FlowDirection="RightToLeft"` on root (cascades) |

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| C# learning curve | Medium | C# is very similar to Java/TypeScript; XAML is intuitive |
| Firebase .NET libraries less mature | Low | `FirebaseDatabase.net` is stable; worst case use REST directly |
| Print monitor P/Invoke complexity | Low | C# P/Invoke is much cleaner than Python ctypes |
| Feature parity takes longer than estimated | Medium | Keep PyQt6 version running in parallel; migrate incrementally |
| WebView2 not installed on target PCs | Low | WebView2 bootstrapper auto-installs Edge WebView2 Runtime |
| NSIS installer changes | Low | Same NSIS, just different EXE path |

---

## Recommended Execution Order

```
Week 1:  Phase 1 (Foundation) + Phase 4 (Theme) in parallel
Week 2:  Phase 2 (Business Services) + Phase 5 (Controls) in parallel
Week 3:  Phase 3 (System Services) + Phase 6 starts (Auth + Main windows)
Week 4:  Phase 6 continues (Pages, Dialogs)
Week 5:  Phase 7 (Integration) + Phase 8 (Build)
Week 6:  Phase 9 (Testing) + Bug fixes + Polish
```

**Testing should run continuously alongside each phase, not just at the end.**

---

## Getting Started

### Prerequisites
- .NET 8 SDK
- Visual Studio 2022 or Rider
- WebView2 Runtime (for dev testing)

### First Commands
```bash
# From repo root
cd sionyx-kiosk-wpf

# Create solution and project
dotnet new sln -n SionyxKiosk
dotnet new wpf -n SionyxKiosk -o src/SionyxKiosk
dotnet sln add src/SionyxKiosk/SionyxKiosk.csproj

# Create test project
dotnet new xunit -n SionyxKiosk.Tests -o tests/SionyxKiosk.Tests
dotnet sln add tests/SionyxKiosk.Tests/SionyxKiosk.Tests.csproj
dotnet add tests/SionyxKiosk.Tests reference src/SionyxKiosk/SionyxKiosk.csproj

# Add core packages
cd src/SionyxKiosk
dotnet add package MaterialDesignThemes
dotnet add package MaterialDesignColors
dotnet add package CommunityToolkit.Mvvm
dotnet add package Microsoft.Extensions.Hosting
dotnet add package Microsoft.Extensions.DependencyInjection
dotnet add package FirebaseDatabase.net
dotnet add package FirebaseAuthentication.net
dotnet add package Microsoft.Web.WebView2
dotnet add package Serilog
dotnet add package Serilog.Sinks.File
dotnet add package Serilog.Sinks.Console

# Test packages
cd ../../tests/SionyxKiosk.Tests
dotnet add package Moq
dotnet add package FluentAssertions
```

---

## Status Tracker

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Foundation | IN PROGRESS | .NET 8 SDK installed, solution scaffolded, all NuGet packages added. Components completed: RegistryConfig, FirebaseConfig, DotEnvLoader, DeviceInfo, AppConstants, ErrorTranslations, PurchaseStatus, LoggingSetup, LocalDatabase, FirebaseClient (auth+RTDB+SSE), SseListener, BaseService. **Build: 0 errors, 0 warnings.** |
| Phase 2: Business Services | NOT STARTED | |
| Phase 3: System Services | NOT STARTED | |
| Phase 4: Theme & Design | NOT STARTED | |
| Phase 5: Reusable Controls | NOT STARTED | |
| Phase 6: Views + ViewModels | NOT STARTED | |
| Phase 7: App Shell | NOT STARTED | |
| Phase 8: Build & Distribution | NOT STARTED | |
| Phase 9: Testing | NOT STARTED | Unit tests pending for Phase 1 |
