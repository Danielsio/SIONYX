using System.Text.Json;
using System.Windows.Threading;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Services;

/// <summary>
/// Checks and enforces organization operating hours.
/// Uses WPF DispatcherTimer instead of QTimer.
/// </summary>
public class OperatingHoursService : BaseService, IDisposable
{
    protected override string ServiceName => "OperatingHoursService";

    // Events replace PyQt signals
    public event Action<int>? HoursEndingSoon;   // minutes until closing
    public event Action<string>? HoursEnded;      // grace behavior
    public event Action<OperatingHoursSettings>? SettingsUpdated;

    public OperatingHoursSettings Settings { get; private set; } = new();
    public bool IsMonitoring { get; private set; }

    private readonly DispatcherTimer _checkTimer;
    private bool _warnedGrace;

    public OperatingHoursService(FirebaseClient firebase) : base(firebase)
    {
        _checkTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(30) };
        _checkTimer.Tick += (_, _) => CheckOperatingHours();
    }

    public async Task LoadSettingsAsync()
    {
        try
        {
            var result = await Firebase.DbGetAsync("metadata/settings/operatingHours");
            if (!result.Success || result.Data is not JsonElement data || data.ValueKind == JsonValueKind.Null)
            {
                Settings = new OperatingHoursSettings();
                return;
            }

            Settings = new OperatingHoursSettings
            {
                Enabled = data.TryGetProperty("enabled", out var en) && en.GetBoolean(),
                StartTime = SafeGet(data, "startTime") ?? "06:00",
                EndTime = SafeGet(data, "endTime") ?? "00:00",
                GracePeriodMinutes = data.TryGetProperty("gracePeriodMinutes", out var gp) && gp.TryGetInt32(out var gpVal) ? gpVal : 5,
                GraceBehavior = SafeGet(data, "graceBehavior") ?? "graceful",
            };

            SettingsUpdated?.Invoke(Settings);
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error loading operating hours");
            Settings = new OperatingHoursSettings();
        }
    }

    public (bool IsAllowed, string? Reason) IsWithinOperatingHours()
    {
        if (!Settings.Enabled) return (true, null);

        var current = DateTime.Now.TimeOfDay;
        if (!TryParseTime(Settings.StartTime, out var start) || !TryParseTime(Settings.EndTime, out var end))
            return (true, null);

        bool isWithin;
        if (start <= end)
            isWithin = current >= start && current <= end;
        else
            isWithin = current >= start || current <= end;

        if (!isWithin)
            return (false, $"שעות הפעילות הן בין {Settings.StartTime} ל-{Settings.EndTime}");

        return (true, null);
    }

    public int GetMinutesUntilClosing()
    {
        if (!Settings.Enabled) return -1;
        if (!TryParseTime(Settings.EndTime, out var end)) return -1;

        var now = DateTime.Now;
        var endTime = now.Date + end;
        if (endTime <= now) endTime = endTime.AddDays(1);

        return (int)(endTime - now).TotalMinutes;
    }

    public void StartMonitoring()
    {
        if (IsMonitoring) return;
        IsMonitoring = true;
        _warnedGrace = false;
        _ = LoadSettingsAsync();
        _checkTimer.Start();
        Logger.Information("Operating hours monitoring started");
    }

    public void StopMonitoring()
    {
        if (!IsMonitoring) return;
        IsMonitoring = false;
        _checkTimer.Stop();
        Logger.Information("Operating hours monitoring stopped");
    }

    public void Dispose()
    {
        StopMonitoring();
        GC.SuppressFinalize(this);
    }

    private void CheckOperatingHours()
    {
        if (!Settings.Enabled) return;

        var (isWithin, _) = IsWithinOperatingHours();
        if (!isWithin)
        {
            Logger.Warning("Operating hours ended");
            HoursEnded?.Invoke(Settings.GraceBehavior);
            return;
        }

        if (!_warnedGrace)
        {
            var minutesLeft = GetMinutesUntilClosing();
            if (minutesLeft > 0 && minutesLeft <= Settings.GracePeriodMinutes)
            {
                _warnedGrace = true;
                Logger.Warning("Operating hours ending in {Minutes} minutes", minutesLeft);
                HoursEndingSoon?.Invoke(minutesLeft);
            }
        }
    }

    private static bool TryParseTime(string timeStr, out TimeSpan result)
    {
        result = TimeSpan.Zero;
        var parts = timeStr.Split(':');
        if (parts.Length != 2) return false;
        if (!int.TryParse(parts[0], out var hour) || !int.TryParse(parts[1], out var minute)) return false;
        result = new TimeSpan(hour, minute, 0);
        return true;
    }
}

/// <summary>
/// Operating hours settings model.
/// </summary>
public class OperatingHoursSettings
{
    public bool Enabled { get; set; }
    public string StartTime { get; set; } = "06:00";
    public string EndTime { get; set; } = "00:00";
    public int GracePeriodMinutes { get; set; } = 5;
    public string GraceBehavior { get; set; } = "graceful";
}
