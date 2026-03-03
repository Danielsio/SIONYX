using System.Media;
using System.Windows;
using Serilog;

namespace SionyxKiosk.Services;

/// <summary>
/// Coordinates session lifecycle events with UI elements (floating timer, notifications).
/// Owns subscription/unsubscription of SessionService, PrintMonitorService, and IdleTimeoutService events.
/// Extracted from App.xaml.cs to reduce god-class complexity.
/// </summary>
public class SessionCoordinator
{
    private static readonly ILogger Logger = Log.ForContext<SessionCoordinator>();

    private readonly SessionService _session;
    private readonly PrintMonitorService _printMonitor;
    private readonly AuthService _auth;
    private readonly PrintHistoryService _printHistory;
    private readonly IdleTimeoutService _idleTimeout;

    private Action? _sessionStartedHandler;
    private Action<int>? _sessionTimeUpdatedHandler;
    private Action<string>? _sessionEndedHandler;
    private Action? _warning5MinHandler;
    private Action? _warning1MinHandler;
    private Action<string>? _syncFailedHandler;
    private Action? _syncRestoredHandler;
    private Action<string, int, double, double>? _printJobAllowedHandler;
    private Action<string, int, double, double>? _printJobBlockedHandler;
    private Action<double>? _printBudgetUpdatedHandler;
    private Action<int>? _idleWarningHandler;
    private Action? _idleTimeoutHandler;
    private Action? _activityResumedHandler;

    private Views.Controls.FloatingTimer? _floatingTimer;

    public event Action? MinimizeMainWindow;
    public event Action? RestoreMainWindow;

    public SessionCoordinator(SessionService session, PrintMonitorService printMonitor,
        AuthService auth, PrintHistoryService printHistory, IdleTimeoutService idleTimeout)
    {
        _session = session;
        _printMonitor = printMonitor;
        _auth = auth;
        _printHistory = printHistory;
        _idleTimeout = idleTimeout;
    }

    /// <summary>Subscribe to all session and print monitor events.</summary>
    public void Subscribe()
    {
        Unsubscribe();

        _sessionStartedHandler = OnSessionStarted;
        _sessionTimeUpdatedHandler = OnTimeUpdated;
        _sessionEndedHandler = OnSessionEnded;
        _warning5MinHandler = OnWarning5Min;
        _warning1MinHandler = OnWarning1Min;
        _syncFailedHandler = _ => Application.Current?.Dispatcher.InvokeAsync(() => _floatingTimer?.SetOfflineMode(true));
        _syncRestoredHandler = () => Application.Current?.Dispatcher.InvokeAsync(() => _floatingTimer?.SetOfflineMode(false));

        _session.SessionStarted += _sessionStartedHandler;
        _session.TimeUpdated += _sessionTimeUpdatedHandler;
        _session.SessionEnded += _sessionEndedHandler;
        _session.Warning5Min += _warning5MinHandler;
        _session.Warning1Min += _warning1MinHandler;
        _session.SyncFailed += _syncFailedHandler;
        _session.SyncRestored += _syncRestoredHandler;

        _printJobAllowedHandler = OnPrintJobAllowed;
        _printJobBlockedHandler = OnPrintJobBlocked;
        _printBudgetUpdatedHandler = budget =>
            Application.Current?.Dispatcher.InvokeAsync(() => _floatingTimer?.UpdatePrintBalance(budget));

        _printMonitor.JobAllowed += _printJobAllowedHandler;
        _printMonitor.JobBlocked += _printJobBlockedHandler;
        _printMonitor.BudgetUpdated += _printBudgetUpdatedHandler;

        _idleWarningHandler = OnIdleWarning;
        _idleTimeoutHandler = OnIdleTimeout;
        _activityResumedHandler = OnActivityResumed;

        _idleTimeout.IdleWarning += _idleWarningHandler;
        _idleTimeout.IdleTimeout += _idleTimeoutHandler;
        _idleTimeout.ActivityResumed += _activityResumedHandler;
    }

    /// <summary>Unsubscribe from all events and close the floating timer.</summary>
    public void Unsubscribe()
    {
        if (_sessionStartedHandler != null) _session.SessionStarted -= _sessionStartedHandler;
        if (_sessionTimeUpdatedHandler != null) _session.TimeUpdated -= _sessionTimeUpdatedHandler;
        if (_sessionEndedHandler != null) _session.SessionEnded -= _sessionEndedHandler;
        if (_warning5MinHandler != null) _session.Warning5Min -= _warning5MinHandler;
        if (_warning1MinHandler != null) _session.Warning1Min -= _warning1MinHandler;
        if (_syncFailedHandler != null) _session.SyncFailed -= _syncFailedHandler;
        if (_syncRestoredHandler != null) _session.SyncRestored -= _syncRestoredHandler;

        if (_printJobAllowedHandler != null) _printMonitor.JobAllowed -= _printJobAllowedHandler;
        if (_printJobBlockedHandler != null) _printMonitor.JobBlocked -= _printJobBlockedHandler;
        if (_printBudgetUpdatedHandler != null) _printMonitor.BudgetUpdated -= _printBudgetUpdatedHandler;

        if (_idleWarningHandler != null) _idleTimeout.IdleWarning -= _idleWarningHandler;
        if (_idleTimeoutHandler != null) _idleTimeout.IdleTimeout -= _idleTimeoutHandler;
        if (_activityResumedHandler != null) _idleTimeout.ActivityResumed -= _activityResumedHandler;

        _sessionStartedHandler = null;
        _sessionTimeUpdatedHandler = null;
        _sessionEndedHandler = null;
        _warning5MinHandler = null;
        _warning1MinHandler = null;
        _syncFailedHandler = null;
        _syncRestoredHandler = null;
        _printJobAllowedHandler = null;
        _printJobBlockedHandler = null;
        _printBudgetUpdatedHandler = null;
        _idleWarningHandler = null;
        _idleTimeoutHandler = null;
        _activityResumedHandler = null;
    }

    /// <summary>Close the floating timer (call during logout/stop).</summary>
    public void CloseFloatingTimer()
    {
        Application.Current?.Dispatcher.InvokeAsync(() =>
        {
            if (_floatingTimer != null)
            {
                _floatingTimer.ReturnRequested -= OnFloatingTimerReturn;
                _floatingTimer.Close();
                _floatingTimer = null;
            }
        });
    }

    /// <summary>Resume the active session: show timer, minimize main window.</summary>
    public void ResumeSession()
    {
        Application.Current?.Dispatcher.InvokeAsync(() =>
        {
            _floatingTimer?.Show();
            MinimizeMainWindow?.Invoke();
        });
    }

    private void OnSessionStarted()
    {
        _printMonitor.StartMonitoring();
        _idleTimeout.StartMonitoring();
        Application.Current?.Dispatcher.InvokeAsync(() =>
        {
            _floatingTimer = new Views.Controls.FloatingTimer();
            _floatingTimer.UpdatePrintBalance(_auth.CurrentUser?.PrintBalance ?? 0);
            _floatingTimer.ReturnRequested += OnFloatingTimerReturn;
            _floatingTimer.Show();
            MinimizeMainWindow?.Invoke();
        });
    }

    private void OnTimeUpdated(int remaining)
    {
        Application.Current?.Dispatcher.InvokeAsync(() =>
        {
            _floatingTimer?.UpdateTime(remaining);
            _floatingTimer?.UpdateUsageTime(_session.TimeUsed);
        });
    }

    private void OnSessionEnded(string reason)
    {
        _printMonitor.StopMonitoring();
        _idleTimeout.StopMonitoring();
        Application.Current?.Dispatcher.InvokeAsync(() =>
        {
            CloseFloatingTimerInternal();
            RestoreMainWindow?.Invoke();
        });
    }

    private void OnWarning5Min()
    {
        Logger.Information("Session warning: 5 minutes remaining");
        PlayAlertSound();
        Views.Controls.FloatingNotification.Show(
            "5 דקות נותרו", "ההפעלה תסתיים בעוד 5 דקות",
            Views.Controls.FloatingNotification.NotificationType.Warning, 5000);
    }

    private void OnWarning1Min()
    {
        Logger.Information("Session warning: 1 minute remaining");
        PlayCriticalSound();
        Views.Controls.FloatingNotification.Show(
            "דקה אחרונה!", "ההפעלה תסתיים בעוד דקה",
            Views.Controls.FloatingNotification.NotificationType.Error, 6000);
    }

    private void OnPrintJobAllowed(string doc, int pages, double cost, double remaining)
    {
        Logger.Information("Print job allowed: '{Doc}' ({Pages}p, {Cost}₪)", doc, pages, cost);
        _printHistory.AddJob(doc, pages, 1, false, cost, "approved", remaining);
        Application.Current?.Dispatcher.InvokeAsync(() => _floatingTimer?.UpdatePrintBalance(remaining));
        Views.Controls.FloatingNotification.Show(
            "הדפסה אושרה", $"{doc} — {cost:F2}₪",
            Views.Controls.FloatingNotification.NotificationType.Success);
    }

    private void OnPrintJobBlocked(string doc, int pages, double cost, double budget)
    {
        Logger.Warning("Print job blocked: '{Doc}' ({Pages}p, {Cost}₪, budget={Budget}₪)", doc, pages, cost, budget);
        _printHistory.AddJob(doc, pages, 1, false, cost, "denied", budget);
        Views.Controls.FloatingNotification.Show(
            "הדפסה נדחתה", $"יתרה לא מספיקה ({budget:F2}₪ זמין, צריך {cost:F2}₪)",
            Views.Controls.FloatingNotification.NotificationType.Error, 5000);
    }

    private void OnFloatingTimerReturn()
    {
        Application.Current?.Dispatcher.InvokeAsync(() =>
        {
            _floatingTimer?.Hide();
            RestoreMainWindow?.Invoke();
        });
    }

    private void OnIdleWarning(int secondsRemaining)
    {
        Logger.Warning("Idle warning: session will end in {Seconds}s if no activity", secondsRemaining);
        PlayAlertSound();
        var minutes = secondsRemaining / 60;
        var label = minutes > 0 ? $"{minutes} דקות" : $"{secondsRemaining} שניות";
        Views.Controls.FloatingNotification.Show(
            "אין פעילות", $"ההפעלה תסתיים בעוד {label} אם לא תהיה פעילות",
            Views.Controls.FloatingNotification.NotificationType.Warning, 8000);
    }

    private void OnIdleTimeout()
    {
        Logger.Warning("Idle timeout reached, ending session");
        PlayCriticalSound();
        Views.Controls.FloatingNotification.Show(
            "ההפעלה הסתיימה", "ההפעלה הסתיימה עקב חוסר פעילות",
            Views.Controls.FloatingNotification.NotificationType.Error, 6000);
        _ = _session.EndSessionAsync("idle");
    }

    private void OnActivityResumed()
    {
        Logger.Information("User activity resumed after idle warning");
        Views.Controls.FloatingNotification.Show(
            "ברוך השב!", "ההפעלה ממשיכה",
            Views.Controls.FloatingNotification.NotificationType.Success, 3000);
    }

    private static void PlayAlertSound()
    {
        try { SystemSounds.Exclamation.Play(); }
        catch { /* non-fatal */ }
    }

    private static void PlayCriticalSound()
    {
        try { SystemSounds.Hand.Play(); }
        catch { /* non-fatal */ }
    }

    private void CloseFloatingTimerInternal()
    {
        if (_floatingTimer != null)
        {
            _floatingTimer.ReturnRequested -= OnFloatingTimerReturn;
            _floatingTimer.Close();
            _floatingTimer = null;
        }
    }
}
