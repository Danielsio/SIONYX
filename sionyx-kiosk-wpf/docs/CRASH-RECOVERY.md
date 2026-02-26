# Crash Recovery — Exploration & Implementation Plan

## Current State

The kiosk app currently has:
- **Crash logging**: `WriteCrashLog()` in `App.xaml.cs` writes crash reports to `logs/crash_*.log`
- **Global exception handlers**: `DispatcherUnhandledException`, `AppDomain.UnhandledException`, `TaskScheduler.UnobservedTaskException`
- **UI recovery**: On unhandled UI exceptions, `ex.Handled = true` prevents app termination and shows the auth window
- **Session sync**: `SessionService` syncs remaining time to Firebase every 30 seconds

## Problem Statement

If the app crashes mid-session:
1. The session timer stops locally but Firebase still shows the session as active
2. The user loses their remaining time until an admin manually intervenes
3. On a kiosk machine, the app needs to restart automatically

## Recovery Strategies

### Option A: Watchdog Process (Recommended)

A lightweight background process (or Windows Service) that monitors the kiosk app and restarts it on crash.

**Pros:**
- Simple to implement (< 100 lines)
- Works for all crash types including CLR fatal errors
- No session logic needed in the watchdog

**Cons:**
- Requires a second process to be installed/managed
- Adds complexity to the installer

**Implementation:**
```csharp
// SionyxWatchdog — a simple .NET console app
while (true)
{
    var process = Process.Start("SionyxKiosk.exe");
    process.WaitForExit();

    // Write restart log
    File.AppendAllText("watchdog.log",
        $"[{DateTime.Now:O}] App exited with code {process.ExitCode}, restarting...\n");

    Thread.Sleep(3000); // brief delay to avoid restart loops
}
```

The scheduled task would run the watchdog instead of the app directly.

### Option B: Session Recovery on Startup (Recommended — use with Option A)

On app startup, check Firebase for an active session that was not cleanly ended.

**Pros:**
- Preserves the user's remaining time across crashes
- Works regardless of crash type

**Implementation:**
1. On `StartSessionAsync`, save `{ sessionId, userId, startTime, remainingTime }` to a local file (`session_state.json`)
2. On `EndSessionAsync`, delete the file
3. On startup, if the file exists:
   - Calculate elapsed time since crash: `elapsed = now - lastSyncTime`
   - Deduct elapsed time from remaining time
   - Either auto-resume the session or show the user their recovered balance
4. Sync corrected time to Firebase

```
session_state.json:
{
  "sessionId": "abc123",
  "userId": "user456",
  "startedAt": "2026-02-22T10:00:00Z",
  "remainingAtStart": 3600,
  "lastTickAt": "2026-02-22T10:15:00Z"
}
```

### Option C: Self-Restart via Exception Handler

In the `DispatcherUnhandledException` handler, attempt to restart the app process.

**Pros:**
- No extra process needed

**Cons:**
- Doesn't work for CLR fatal errors (stack overflow, access violation)
- Can cause restart loops if the crash is deterministic
- Risky: restarting from within a crashing process is inherently fragile

**Not recommended as sole strategy.**

### Option D: Windows Restart Manager Integration

Register with the Windows Restart Manager so the OS restarts the app after a crash.

**Pros:**
- Built into Windows, zero maintenance
- Works for all crash types

**Cons:**
- Only works on Windows 10+ (fine for kiosk)
- Limited control over restart timing
- Requires `RegisterApplicationRestart` P/Invoke

```csharp
[DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
static extern int RegisterApplicationRestart(string commandLine, int flags);

// Call during startup:
RegisterApplicationRestart("--recovered", 0);
```

## Recommended Approach

**Combine Options A + B:**

1. **Watchdog process** ensures the app always restarts after a crash (handles the "get it running again" problem)
2. **Session recovery on startup** ensures the user's time is preserved (handles the "don't lose my money" problem)

### Implementation Priority

| Step | Description | Effort |
|------|-------------|--------|
| 1 | Add `session_state.json` write on session start/tick | Small |
| 2 | Add session recovery logic on startup | Medium |
| 3 | Create watchdog console app | Small |
| 4 | Update installer to run watchdog instead of app directly | Small |
| 5 | Add `RegisterApplicationRestart` as backup | Tiny |
| 6 | Add crash count tracking to detect restart loops | Small |

### Restart Loop Protection

To prevent infinite restart loops:
- Track crash timestamps in a file
- If > 3 crashes within 5 minutes, stop restarting and log an alert
- The admin can see the crash logs and investigate

## Testing Strategy

1. Unit test session state serialization/deserialization
2. Unit test time-loss calculation after simulated crash
3. Integration test: kill the app process mid-session, verify recovery on restart
4. Stress test: rapid crash/restart cycles to verify loop protection
