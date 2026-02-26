# SIONYX Web Admin — Audit & Roadmap

## Bugs to Fix

| # | Issue | File | Severity | Status |
|---|-------|------|----------|--------|
| W1 | `MessagesPage` — `user.uid` can be undefined when calling `sendMessage` | `pages/MessagesPage.jsx:141` | Medium | Open |
| W2 | `ComputersPage` — no `orgId` check before loading data, causes invalid Firebase paths | `pages/ComputersPage.jsx:71` | Medium | Open |
| W3 | `OverviewPage` — revenue chart uses synthetic/mock data, misleading | `pages/OverviewPage.jsx:154` | Medium | Open |
| W4 | `OverviewPage` — `loadData` not cancelled on unmount, stale state updates | `pages/OverviewPage.jsx:93` | Low | Open |
| W5 | `UsersPage` — `handleSendMessage` may use stale `selectedUser` after drawer closes | `pages/UsersPage.jsx:397` | Low | Open |
| W6 | `PackagesPage` — `confirmLoading` uses `loading` instead of dedicated submitting state | `pages/PackagesPage.jsx:392` | Low | Open |
| W7 | `csvExport` — double `.csv.csv` extension if caller includes `.csv` in filename | `utils/csvExport.js:23` | Low | Open |

## UX Improvements

| # | Improvement | Priority |
|---|-------------|----------|
| U1 | Standardize empty states across all pages (shared `EmptyState` component) | Medium |
| U2 | `AnnouncementsPage` — add loading state to toggle active button to prevent double-clicks | Medium |
| U3 | `UsersPage` — skeleton/loading state for drawer content while purchases load | Low |
| U4 | `UsersPage` — search input full-width on mobile instead of fixed `maxWidth: 500` | Low |
| U5 | Add `aria-label` to all icon-only buttons for accessibility | Low |
| U6 | Footer "terms of use" and "privacy policy" links are placeholders (`href='#'`) — add real pages or remove | Low |
| U7 | Login page — add client-side cooldown/debounce after failed login attempts | Low |

## Code Quality

| # | Issue | Priority |
|---|-------|----------|
| C1 | Duplicated `useIsMobile` hook in 3 files — extract to `hooks/useIsMobile.js` | Medium |
| C2 | Inconsistent error handling patterns (some `message.error()`, some `setError()`, some both) | Medium |
| C3 | `loadData` functions not memoized with `useCallback`, can cause stale closures | Low |
| C4 | Duplicated time formatting logic across pages — consolidate to `timeFormatter.js` | Low |
| C5 | TODO in `ErrorBoundary.jsx` — integrate Sentry or remove comment | Low |

## Feature Proposals

| # | Feature | Description | Effort |
|---|---------|-------------|--------|
| F1 | Real revenue chart | Replace mock data with real daily/weekly purchase data | Medium |
| F2 | Additional metrics | Peak hours, user retention, conversion funnel, print trends | Large |
| F3 | Admin activity logs | Log all admin actions (balance changes, kicks, role changes) for audit trail | Medium |
| F4 | Export improvements | Add PDF/Excel export for users, purchases, packages | Medium |
| F5 | Real-time updates | Use Firebase listeners instead of manual refresh for users/messages/computers | Medium |
| F6 | Scheduled announcements | Start/end dates for system announcements | Small |
| F7 | Bulk actions | Bulk message send, bulk balance adjustment, bulk package activation | Medium |
| F8 | Search/filter enhancements | Filter users by status, date range, package on UsersPage | Small |
| F9 | Dashboard customization | Configurable widgets/layout for overview page | Large |
| F10 | Notification system | In-app notifications for new messages, low balances, system events | Medium |

## Metrics to Add (Overview Page)

| Metric | Description |
|--------|-------------|
| Revenue over time | Real daily/weekly/monthly revenue from purchases |
| Peak usage hours | Busiest hours/days from session data |
| User retention | New vs returning users, churn rate |
| Package popularity trends | Package sales over time |
| Period comparisons | Day-over-day, week-over-week, month-over-month |
| Session duration distribution | Histogram of session lengths |
| Revenue by package | Revenue breakdown per package |
| Print usage trends | Print budget consumption over time |
| Computer utilization | Usage % per computer |
| Conversion funnel | Registrations → first purchase → repeat purchase |

## Security Notes

| # | Issue | Priority |
|---|-------|----------|
| S1 | `ProtectedRoute` — only checks `isAuthenticated`, not admin role (defense in depth) | Low |
| S2 | Persisted auth state — if user removed from org, cached auth persists until refresh | Low |
| S3 | Firebase rules — may not cover `role` field (only `isAdmin`), verify alignment | Low |
| S4 | NEDARIM credentials — base64 encoding is not encryption, consider Cloud KMS | Low |
