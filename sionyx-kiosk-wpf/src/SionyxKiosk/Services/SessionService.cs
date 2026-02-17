using System.Text.Json;
using System.Windows.Threading;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Services;

/// <summary>
/// Manages user sessions with Firebase sync, countdown, warnings,
/// print monitoring, operating hours, and session lifecycle.
/// Replaces both session_service.py and session_manager.py.
/// </summary>
public class SessionService : BaseService, IDisposable
{
    protected override string ServiceName => "SessionService";

    private readonly ComputerService _computerService;
    private string _userId;
    private readonly string _orgId;

    // Sub-services
    public OperatingHoursService OperatingHours { get; }

    // Session state
    public string? SessionId { get; private set; }
    public bool IsActive { get; private set; }
    public int RemainingTime { get; private set; }
    public int TimeUsed { get; private set; }
    public DateTime? StartTime { get; private set; }

    // Wall-clock anchor for drift-free countdown
    private int _initialRemainingTime;

    // Sync state
    private int _consecutiveSyncFailures;
    public bool IsOnline { get; private set; } = true;

    // Timers (WPF DispatcherTimer for UI thread safety)
    private readonly DispatcherTimer _countdownTimer;
    private readonly DispatcherTimer _syncTimer;

    // Warning flags
    private bool _warned5Min;
    private bool _warned1Min;

    // Events (replace PyQt signals)
    public event Action? SessionStarted;
    public event Action<int>? TimeUpdated;           // remaining seconds
    public event Action<string>? SessionEnded;        // reason: expired, user, error, hours
    public event Action? Warning5Min;
    public event Action? Warning1Min;
    public event Action<string>? SyncFailed;          // error message
    public event Action? SyncRestored;
    public event Action<int>? OperatingHoursWarning;  // minutes until closing
    public event Action<string>? OperatingHoursEnded;  // grace behavior

    public SessionService(FirebaseClient firebase, string userId, string orgId)
        : base(firebase)
    {
        _userId = userId;
        _orgId = orgId;
        _computerService = new ComputerService(firebase);

        // Operating hours
        OperatingHours = new OperatingHoursService(firebase);
        OperatingHours.HoursEndingSoon += OnHoursEndingSoon;
        OperatingHours.HoursEnded += OnHoursEnded;

        // Tick at 250ms so the display never visually skips seconds,
        // even when the UI thread is briefly busy with animations/rendering.
        _countdownTimer = new DispatcherTimer(DispatcherPriority.Render)
        {
            Interval = TimeSpan.FromMilliseconds(250)
        };
        _countdownTimer.Tick += (_, _) => OnCountdownTick();

        _syncTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(60) };
        _syncTimer.Tick += (_, _) => _ = SyncToFirebaseAsync();

        Logger.Information("Session service initialized for user: {UserId}", userId);
    }

    /// <summary>Update userId for a new login session (singleton reuse).</summary>
    public void Reinitialize(string userId)
    {
        _userId = userId;
        Logger.Information("Session service re-initialized for user: {UserId}", userId);
    }

    /// <summary>Start a new session with the user's remaining time.</summary>
    public async Task<ServiceResult> StartSessionAsync(int initialRemainingTime)
    {
        if (IsActive) return Error("Session already active");

        // Check time expiration
        var expired = await CheckTimeExpirationAsync();
        if (expired) return Error("הזמן שלך פג תוקף. אנא רכוש חבילה חדשה.");

        if (initialRemainingTime <= 0) return Error("No time remaining");

        // Clean up previous processes
        await Task.Run(() =>
        {
            var cleanup = new ProcessCleanupService();
            cleanup.CleanupUserProcesses();
        });

        // Mark session active in Firebase
        var now = DateTime.Now.ToString("o");
        var result = await Firebase.DbUpdateAsync($"users/{_userId}", new
        {
            isSessionActive = true,
            sessionStartTime = now,
            updatedAt = now,
        });

        if (!result.Success) return Error("Failed to start session");

        // Initialize local state
        SessionId = Guid.NewGuid().ToString("N");
        _initialRemainingTime = initialRemainingTime;
        RemainingTime = initialRemainingTime;
        TimeUsed = 0;
        StartTime = DateTime.UtcNow;
        IsActive = true;
        _warned5Min = false;
        _warned1Min = false;

        // Start timers
        _countdownTimer.Start();
        _syncTimer.Start();

        // Start operating hours
        OperatingHours.StartMonitoring();

        Logger.Information("Session started (remaining: {Time}s)", initialRemainingTime);
        SessionStarted?.Invoke();
        return Success(new { SessionId });
    }

    /// <summary>End the current session.</summary>
    public async Task<ServiceResult> EndSessionAsync(string reason = "user")
    {
        if (!IsActive) return Error("No active session");

        Logger.Information("Ending session: {Reason}", reason);

        // Stop timers
        _countdownTimer.Stop();
        _syncTimer.Stop();

        // Stop monitoring
        OperatingHours.StopMonitoring();

        // Final sync
        await FinalSyncAsync(reason);

        // Browser cleanup (async in background)
        await Task.Run(() =>
        {
            var browserCleanup = new BrowserCleanupService();
            browserCleanup.CleanupWithBrowserClose();
        });

        IsActive = false;
        SessionEnded?.Invoke(reason);

        Logger.Information("Session ended (used: {TimeUsed}s)", TimeUsed);
        return Success(new { TimeUsed, RemainingTime });
    }

    public void Dispose()
    {
        _countdownTimer.Stop();
        _syncTimer.Stop();
        OperatingHours.Dispose();
        GC.SuppressFinalize(this);
    }

    // ==================== PRIVATE HELPERS ====================

    private void OnCountdownTick()
    {
        if (!IsActive || StartTime == null) return;

        // Derive from wall-clock — immune to DispatcherTimer drift
        var elapsed = (int)(DateTime.UtcNow - StartTime.Value).TotalSeconds;
        var newRemaining = Math.Max(0, _initialRemainingTime - elapsed);

        // Only push UI updates when the displayed second actually changes
        if (newRemaining == RemainingTime && elapsed == TimeUsed) return;

        TimeUsed = elapsed;
        RemainingTime = newRemaining;
        TimeUpdated?.Invoke(RemainingTime);

        if (RemainingTime <= 300 && !_warned5Min)
        {
            _warned5Min = true;
            Warning5Min?.Invoke();
        }
        if (RemainingTime <= 60 && !_warned1Min)
        {
            _warned1Min = true;
            Warning1Min?.Invoke();
        }
        if (RemainingTime <= 0)
        {
            _ = EndSessionAsync("expired");
        }
    }

    private async Task SyncToFirebaseAsync()
    {
        if (!IsActive) return;

        var result = await Firebase.DbUpdateAsync($"users/{_userId}", new
        {
            remainingTime = RemainingTime,
            updatedAt = DateTime.Now.ToString("o"),
        });

        if (result.Success)
        {
            if (_consecutiveSyncFailures > 0)
            {
                _consecutiveSyncFailures = 0;
                IsOnline = true;
                SyncRestored?.Invoke();
            }
        }
        else
        {
            _consecutiveSyncFailures++;
            Logger.Error("Sync failed ({Count} consecutive)", _consecutiveSyncFailures);
            if (_consecutiveSyncFailures >= 3)
            {
                IsOnline = false;
                SyncFailed?.Invoke("Connection lost");
            }
        }
    }

    private async Task FinalSyncAsync(string reason)
    {
        await Firebase.DbUpdateAsync($"users/{_userId}", new Dictionary<string, object?>
        {
            ["remainingTime"] = Math.Max(0, RemainingTime),
            ["isSessionActive"] = false,
            ["sessionStartTime"] = null,
            ["updatedAt"] = DateTime.Now.ToString("o"),
        });
    }

    private async Task<bool> CheckTimeExpirationAsync()
    {
        try
        {
            var result = await Firebase.DbGetAsync($"users/{_userId}");
            if (!result.Success || result.Data is not JsonElement data || data.ValueKind == JsonValueKind.Null)
                return false;

            var expiresAtStr = data.TryGetProperty("timeExpiresAt", out var te) ? te.GetString() : null;
            if (string.IsNullOrEmpty(expiresAtStr)) return false;
            if (!DateTime.TryParse(expiresAtStr, out var expiresAt)) return false;

            if (DateTime.Now <= expiresAt) return false;

            // Time expired - reset to 0
            await Firebase.DbUpdateAsync($"users/{_userId}", new Dictionary<string, object?>
            {
                ["remainingTime"] = 0,
                ["timeExpiresAt"] = null,
                ["updatedAt"] = DateTime.Now.ToString("o"),
            });
            return true;
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error checking time expiration");
            return false;
        }
    }

    private void OnHoursEndingSoon(int minutes)
    {
        Logger.Warning("Operating hours ending in {Minutes} minutes", minutes);
        OperatingHoursWarning?.Invoke(minutes);
    }

    private void OnHoursEnded(string graceBehavior)
    {
        Logger.Warning("Operating hours ended, behavior: {Behavior}", graceBehavior);
        OperatingHoursEnded?.Invoke(graceBehavior);

        var reason = graceBehavior == "force" ? "hours_force" : "hours";
        _ = EndSessionAsync(reason);
    }
}
