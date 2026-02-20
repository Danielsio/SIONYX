using System.Windows;
using Serilog;

namespace SionyxKiosk.Services;

/// <summary>
/// Coordinates session lifecycle events with UI elements (floating timer, notifications).
/// Owns subscription/unsubscription of SessionService and PrintMonitorService events.
/// Extracted from App.xaml.cs to reduce god-class complexity.
/// </summary>
public class SessionCoordinator
{
    private static readonly ILogger Logger = Log.ForContext<SessionCoordinator>();

    private readonly SessionService _session;
    private readonly PrintMonitorService _printMonitor;
    private readonly AuthService _auth;

    // Handler references for proper unsubscription
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

    private Views.Controls.FloatingTimer? _floatingTimer;

    /// <summary>Called when we need to minimize the main window.</summary>
    public event Action? MinimizeMainWindow;
    /// <summary>Called when we need to restore the main window.</summary>
    public event Action? RestoreMainWindow;

    public SessionCoordinator(SessionService session, PrintMonitorService printMonitor, AuthService auth)
    {
        _session = session;
        _printMonitor = printMonitor;
        _auth = auth;
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
        _syncFailedHandler = _ => Application.Current?.Dispatcher.Invoke(() => _floatingTimer?.SetOfflineMode(true));
        _syncRestoredHandler = () => Application.Current?.Dispatcher.Invoke(() => _floatingTimer?.SetOfflineMode(false));

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
            Application.Current?.Dispatcher.Invoke(() => _floatingTimer?.UpdatePrintBalance(budget));

        _printMonitor.JobAllowed += _printJobAllowedHandler;
        _printMonitor.JobBlocked += _printJobBlockedHandler;
        _printMonitor.BudgetUpdated += _printBudgetUpdatedHandler;
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
    }

    /// <summary>Close the floating timer (call during logout/stop).</summary>
    public void CloseFloatingTimer()
    {
        Application.Current?.Dispatcher.Invoke(() =>
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
        Application.Current?.Dispatcher.Invoke(() =>
        {
            _floatingTimer?.Show();
            MinimizeMainWindow?.Invoke();
        });
    }

    private void OnSessionStarted()
    {
        _printMonitor.StartMonitoring();
        Application.Current?.Dispatcher.Invoke(() =>
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
        Application.Current?.Dispatcher.Invoke(() =>
        {
            _floatingTimer?.UpdateTime(remaining);
            _floatingTimer?.UpdateUsageTime(_session.TimeUsed);
        });
    }

    private void OnSessionEnded(string reason)
    {
        _printMonitor.StopMonitoring();
        Application.Current?.Dispatcher.Invoke(() =>
        {
            CloseFloatingTimerInternal();
            RestoreMainWindow?.Invoke();
        });
    }

    private void OnWarning5Min()
    {
        Logger.Information("Session warning: 5 minutes remaining");
        Views.Controls.FloatingNotification.Show(
            "5 דקות נותרו", "ההפעלה תסתיים בעוד 5 דקות",
            Views.Controls.FloatingNotification.NotificationType.Warning, 5000);
    }

    private void OnWarning1Min()
    {
        Logger.Information("Session warning: 1 minute remaining");
        Views.Controls.FloatingNotification.Show(
            "דקה אחרונה!", "ההפעלה תסתיים בעוד דקה",
            Views.Controls.FloatingNotification.NotificationType.Error, 6000);
    }

    private void OnPrintJobAllowed(string doc, int pages, double cost, double remaining)
    {
        Logger.Information("Print job allowed: '{Doc}' ({Pages}p, {Cost}₪)", doc, pages, cost);
        Application.Current?.Dispatcher.Invoke(() => _floatingTimer?.UpdatePrintBalance(remaining));
        Views.Controls.FloatingNotification.Show(
            "הדפסה אושרה", $"{doc} — {cost:F2}₪",
            Views.Controls.FloatingNotification.NotificationType.Success);
    }

    private void OnPrintJobBlocked(string doc, int pages, double cost, double budget)
    {
        Logger.Warning("Print job blocked: '{Doc}' ({Pages}p, {Cost}₪, budget={Budget}₪)", doc, pages, cost, budget);
        Views.Controls.FloatingNotification.Show(
            "הדפסה נדחתה", $"יתרה לא מספיקה ({budget:F2}₪ זמין, צריך {cost:F2}₪)",
            Views.Controls.FloatingNotification.NotificationType.Error, 5000);
    }

    private void OnFloatingTimerReturn()
    {
        Application.Current?.Dispatcher.Invoke(() =>
        {
            _floatingTimer?.Hide();
            RestoreMainWindow?.Invoke();
        });
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
