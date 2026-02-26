# Print Job History — Exploration & Implementation Plan

## Overview

Add a page to the kiosk app showing the user's print job history: what they printed, when, page count, cost, and status (approved/denied).

## Current Architecture

The `PrintMonitorService` already intercepts every print job and:
- Pauses the job in the spooler
- Reads page count, copies, and color mode from DEVMODE
- Calculates cost based on per-page pricing from Firebase
- Approves (resumes) or denies (cancels) based on remaining print budget
- Fires `JobAllowed` / `JobBlocked` events with `(docName, pages, cost, remainingBudget)`
- Updates the user's print balance in Firebase under `users/{userId}/printBalance`

Currently, **no history is persisted** — once the events are consumed by `SessionCoordinator` (for floating notifications), the data is gone.

## Data Model

### Option A: Firebase RTDB (Simple, but adds read/write cost)

```
organizations/{orgId}/printHistory/{userId}/{historyId}:
{
  "documentName": "Report.pdf",
  "pages": 5,
  "copies": 1,
  "isColor": false,
  "cost": 5.0,
  "status": "approved",         // "approved" | "denied"
  "remainingAfter": 45.0,
  "timestamp": 1708617600000,
  "printerName": "HP LaserJet"
}
```

**Pros:** Accessible from web admin for reporting. Persists across reinstalls.
**Cons:** Adds Firebase RTDB usage. The user said to reduce RTDB data, so this should be lightweight — only keep recent history and auto-purge old records.

### Option B: Local SQLite Database

Store print history locally on each kiosk machine.

**Pros:** Zero Firebase cost. Fast queries. No network dependency.
**Cons:** Data lost on reinstall. Not visible to admin. Each machine has its own history.

### Option C: Hybrid — Local + Periodic Firebase Sync

Store locally for fast display, sync summaries (daily totals) to Firebase.

**Pros:** Best of both worlds.
**Cons:** More complex.

## Recommended Approach: Option A (Firebase RTDB, with auto-cleanup)

Given that the kiosk is always online and the admin might want to see print usage reports, Firebase RTDB is the natural choice. To minimize data:
- Keep only the last 50 print jobs per user
- Auto-purge records older than 30 days
- Each record is ~200 bytes, so 50 records = ~10 KB per user (negligible)

## Implementation Plan

### Step 1: PrintHistoryService (New Service)

```csharp
public class PrintHistoryService : BaseService
{
    private string _userId;
    private const int MaxHistorySize = 50;

    public async Task RecordJobAsync(PrintJobRecord job) { ... }
    public async Task<List<PrintJobRecord>> GetHistoryAsync() { ... }
    public async Task CleanupOldRecordsAsync(int retentionDays = 30) { ... }
}

public record PrintJobRecord(
    string Id,
    string DocumentName,
    int Pages,
    int Copies,
    bool IsColor,
    double Cost,
    string Status,       // "approved" | "denied"
    double RemainingAfter,
    long Timestamp,
    string PrinterName
);
```

### Step 2: Hook Into PrintMonitorService

In `SessionCoordinator`, after `JobAllowed` / `JobBlocked` events:

```csharp
_printJobAllowedHandler = (doc, pages, cost, remaining) =>
{
    _ = _printHistory.RecordJobAsync(new PrintJobRecord(
        Id: Guid.NewGuid().ToString("N")[..12],
        DocumentName: doc,
        Pages: pages,
        Copies: 1,
        IsColor: false,  // extend event args to pass this
        Cost: cost,
        Status: "approved",
        RemainingAfter: remaining,
        Timestamp: DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
        PrinterName: ""   // extend event args
    ));
    // ... existing notification code
};
```

### Step 3: PrintHistoryViewModel

```csharp
public partial class PrintHistoryViewModel : ObservableObject
{
    [ObservableProperty] private ObservableCollection<PrintJobRecord> _jobs;
    [ObservableProperty] private bool _isLoading;
    [ObservableProperty] private double _totalCost;
    [ObservableProperty] private int _totalPages;

    [RelayCommand]
    private async Task LoadHistoryAsync() { ... }
}
```

### Step 4: PrintHistoryPage (New XAML Page)

UI layout:
```
┌──────────────────────────────────────────────┐
│  📄  היסטוריית הדפסות                        │
├──────────────────────────────────────────────┤
│  Summary Cards:                              │
│  [Total Pages: 127]  [Total Cost: 45.50₪]   │
│  [Approved: 24]      [Denied: 3]             │
├──────────────────────────────────────────────┤
│  List of print jobs (newest first):          │
│                                              │
│  📄 Report.pdf                               │
│  5 עמודים • שחור-לבן • 5.00₪ • ✅ אושר      │
│  22/02/2026 10:15                            │
│  ─────────────────────────────────           │
│  📄 Photo.png                                │
│  1 עמוד • צבעוני • 3.00₪ • ✅ אושר           │
│  22/02/2026 09:30                            │
│  ─────────────────────────────────           │
│  📄 LargeDoc.pdf                             │
│  50 עמודים • שחור-לבן • 50.00₪ • ❌ נדחה    │
│  21/02/2026 16:45                            │
└──────────────────────────────────────────────┘
```

### Step 5: Navigation

Add a sidebar entry with icon "📄" and label "היסטוריית הדפסות" in `MainWindow.xaml`.

### Step 6: PrintMonitorService Event Args Enhancement

Extend `JobAllowed` and `JobBlocked` events to pass richer data:

```csharp
public record PrintJobEventArgs(
    string DocumentName,
    int Pages,
    int Copies,
    bool IsColor,
    double Cost,
    double RemainingBudget,
    string PrinterName
);

public event Action<PrintJobEventArgs>? JobAllowed;
public event Action<PrintJobEventArgs>? JobBlocked;
```

This is a breaking change to the event signature — `SessionCoordinator` handlers need updating.

## Effort Estimate

| Step | Description | Effort |
|------|-------------|--------|
| 1 | PrintHistoryService | Small |
| 2 | Hook into SessionCoordinator | Small |
| 3 | PrintHistoryViewModel | Small |
| 4 | PrintHistoryPage XAML | Medium |
| 5 | Navigation sidebar entry | Tiny |
| 6 | Event args enhancement | Small |
| 7 | Auto-cleanup (30-day purge) | Small |
| 8 | Tests | Medium |

**Total: ~1-2 days of focused work**

## Firebase Security Rules

```json
{
  "printHistory": {
    "$userId": {
      ".read": "auth != null && ($userId === auth.uid || root.child('users/' + auth.uid + '/role').val() === 'admin')",
      ".write": "auth != null && $userId === auth.uid"
    }
  }
}
```

## Future Enhancements

- **Web admin print reports**: Show per-user and aggregate print statistics
- **Export to CSV**: Allow admin to download print history
- **Print quotas**: Set daily/monthly page limits per user
- **Printer-specific pricing**: Different rates for different printers
