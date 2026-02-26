# SIONYX Kiosk Desktop App — Audit & Roadmap

## Bugs to Fix

| # | Issue | File | Severity | Status |
|---|-------|------|----------|--------|
| K1 | Firebase path duplication — `GetPrintPricingAsync` uses `organizations/{orgId}/metadata` but `FirebaseClient.GetOrgPath()` already prepends it, creating a double path | `Services/OrganizationMetadataService.cs:64,85` | Critical | Open |
| K2 | `ChatService.MarkAllMessagesAsReadAsync` — flat keys `messages/{id}/read` are treated literally by Firebase REST PATCH instead of nested paths | `Services/ChatService.cs:97` | High | Open |
| K3 | `ForceLogoutService.StartListening` — `async void` method, exceptions are unobserved and can crash the process | `Services/ForceLogoutService.cs:27` | Medium | Open |
| K4 | `SseListener.Stop` — synchronous `Wait(500ms)` can block the UI thread when closing PaymentDialog | `Infrastructure/SseListener.cs:63` | Low | Open |
| K5 | PaymentDialog SSE callback — potential null reference on `data.Value` if timing is off | `Views/Dialogs/PaymentDialog.xaml.cs:256` | Low | Open |

## UX Improvements

| # | Improvement | Priority |
|---|-------------|----------|
| U1 | "Start Session" button lacks visible loading state (spinner is below, may be off-screen) | Medium |
| U2 | Phone input has no format validation before API call — show clear error for invalid formats | Low |
| U3 | Packages page has no loading indicator while packages load | Low |
| U4 | Add `AutomationProperties.Name` to important controls for screen reader accessibility | Low |

## Code Quality

| # | Issue | Priority |
|---|-------|----------|
| C1 | Inconsistent Firebase paths — `OrganizationMetadataService` uses full paths while `PrintMonitorService` uses relative `"metadata"` | Medium |
| C2 | `GetPrintPricingAsync` / `SetPrintPricingAsync` appear unused by the kiosk (only used in tests) while `PrintMonitorService` reads pricing directly | Low |
| C3 | Missing XML docs on several public APIs (`SessionCoordinator.Subscribe`, `SystemServicesManager.Start`, etc.) | Low |
| C4 | `HomePage.xaml.cs` mixes UI and flow logic (`EndSession_Click`, `ResumeSession_Click` with `AlertDialog.Confirm`) — should be in ViewModel via commands | Low |
| C5 | `Dispatcher.Invoke` used where `Dispatcher.InvokeAsync` would avoid blocking (HomePage toast) | Low |

## Feature Proposals

| # | Feature | Description | Effort |
|---|---------|-------------|--------|
| F1 | Offline resilience | Add write queue for session updates with exponential backoff retry when connection restores | Large |
| F2 | Crash recovery | On startup, detect abruptly ended sessions and offer to restore or clean up | Medium |
| F3 | Telemetry / analytics | Optional privacy-conscious analytics for sessions, purchases, print jobs, errors | Medium |
| F4 | Print queue view | Show pending/blocked print jobs in a queue view instead of individual approve/deny | Small |
| F5 | Multi-monitor support | Use correct screen for FloatingTimer and dialogs on multi-monitor setups | Small |
| F6 | Auto-update mechanism | Check for new versions on startup and offer in-app update | Large |
| F7 | User feedback system | Allow users to submit feedback/issues from the kiosk | Small |
| F8 | Session history | Show user's recent session history (duration, date, usage) | Medium |

## Security

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| S1 | Default admin password `sionyx2025` in `AppConstants.cs` — used if registry/env not set, could be exploited in production | High | Open |
| S2 | `LocalFileServer` CORS set to `*` — limited risk (localhost only) but could be restricted to actual origin | Low | Open |
| S3 | Document kiosk escape vectors (Ctrl+Alt+Space admin exit, process restrictions coverage) | Low | Open |
| S4 | Path traversal on `LocalFileServer` — already mitigated with `StartsWith` check | N/A | Handled |

## Architecture Notes

- **DI and lifetimes:** Services are singletons with `Reinitialize(userId)`. This works but `HomeViewModel` creation assumes `auth.CurrentUser` is non-null — defensive check recommended.
- **MVVM consistency:** Most logic is in ViewModels, but some click handlers in `HomePage.xaml.cs` mix UI and flow logic. Consider moving to ViewModel commands.
- **No circular dependencies:** Dependency flow is clean: App → Services → ViewModels → Views.
- **Session coordinator pattern:** Well-structured with `Subscribe` for monitoring — good architecture.

## Priority Order

1. **K1** — Fix Firebase path duplication (Critical, prevents pricing from working correctly)
2. **K2** — Fix ChatService batch update structure (High, messages not marked as read)
3. **S1** — Harden default admin password handling for production
4. **K3** — Change `ForceLogoutService.StartListening` to `async Task`
5. **F1** — Offline resilience (most impactful feature for kiosk reliability)
