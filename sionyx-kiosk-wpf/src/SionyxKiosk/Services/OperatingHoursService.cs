using System.Text.Json;
using System.Windows.Threading;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Services;

public class OperatingHoursService : BaseService, IDisposable
{
    protected override string ServiceName => "OperatingHoursService";

    public event Action<int>? HoursEndingSoon;
    public event Action<string>? HoursEnded;
    public event Action<OperatingHoursSettings>? SettingsUpdated;

    public OperatingHoursSettings Settings { get; private set; } = new();
    public bool IsMonitoring { get; private set; }

    private readonly DispatcherTimer _checkTimer;
    private bool _warnedGrace;

    private static readonly string[] DayKeys = { "sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday" };

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

            if (data.TryGetProperty("schedule", out var scheduleEl) && scheduleEl.ValueKind == JsonValueKind.Object)
            {
                foreach (var dayKey in DayKeys)
                {
                    if (scheduleEl.TryGetProperty(dayKey, out var dayEl) && dayEl.ValueKind == JsonValueKind.Object)
                    {
                        Settings.Schedule[dayKey] = new DaySchedule
                        {
                            Open = !dayEl.TryGetProperty("open", out var o) || o.GetBoolean(),
                            StartTime = SafeGet(dayEl, "startTime") ?? "08:00",
                            EndTime = SafeGet(dayEl, "endTime") ?? "22:00",
                        };
                    }
                }
            }

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

        var today = GetTodaySchedule();
        if (today == null) return (true, null);

        if (!today.Open)
            return (false, "היום סגור");

        var current = DateTime.Now.TimeOfDay;
        if (!TryParseTime(today.StartTime, out var start) || !TryParseTime(today.EndTime, out var end))
            return (true, null);

        bool isWithin;
        if (start <= end)
            isWithin = current >= start && current <= end;
        else
            isWithin = current >= start || current <= end;

        if (!isWithin)
            return (false, $"שעות הפעילות היום הן {today.StartTime} - {today.EndTime}");

        return (true, null);
    }

    public int GetMinutesUntilClosing()
    {
        if (!Settings.Enabled) return -1;

        var today = GetTodaySchedule();
        if (today == null || !today.Open) return -1;
        if (!TryParseTime(today.EndTime, out var end)) return -1;

        var now = DateTime.Now;
        var endTime = now.Date + end;
        if (endTime <= now) endTime = endTime.AddDays(1);

        return (int)(endTime - now).TotalMinutes;
    }

    /// <summary>
    /// Returns the schedule for today based on the day of week.
    /// Falls back to the global StartTime/EndTime if no per-day schedule exists.
    /// </summary>
    public DaySchedule? GetTodaySchedule()
    {
        int dow = (int)DateTime.Now.DayOfWeek;
        string dayKey = DayKeys[dow];

        if (Settings.Schedule.TryGetValue(dayKey, out var ds))
            return ds;

        return new DaySchedule
        {
            Open = true,
            StartTime = Settings.StartTime,
            EndTime = Settings.EndTime,
        };
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

public class DaySchedule
{
    public bool Open { get; set; } = true;
    public string StartTime { get; set; } = "08:00";
    public string EndTime { get; set; } = "22:00";
}

public class OperatingHoursSettings
{
    public bool Enabled { get; set; }
    public string StartTime { get; set; } = "06:00";
    public string EndTime { get; set; } = "00:00";
    public int GracePeriodMinutes { get; set; } = 5;
    public string GraceBehavior { get; set; } = "graceful";
    public Dictionary<string, DaySchedule> Schedule { get; set; } = new();
}
