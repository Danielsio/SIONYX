namespace SionyxKiosk.Services;

public interface ISessionService : IDisposable
{
    string? SessionId { get; }
    bool IsActive { get; }
    int RemainingTime { get; }
    int TimeUsed { get; }
    DateTime? StartTime { get; }
    bool IsOnline { get; }
    OperatingHoursService OperatingHours { get; }

    event Action? SessionStarted;
    event Action<int>? TimeUpdated;
    event Action<string>? SessionEnded;
    event Action? Warning5Min;
    event Action? Warning1Min;
    event Action<string>? SyncFailed;
    event Action? SyncRestored;
    event Action<int>? OperatingHoursWarning;
    event Action<string>? OperatingHoursEnded;

    void Reinitialize(string userId);
    Task<ServiceResult> StartSessionAsync(int initialRemainingTime);
    Task<ServiceResult> EndSessionAsync(string reason = "user");
}
