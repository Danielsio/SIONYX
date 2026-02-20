namespace SionyxKiosk.Services;

public interface IChatService : IDisposable
{
    bool IsListening { get; }

    event Action<List<Dictionary<string, object?>>>? MessagesReceived;

    void Reinitialize(string userId);
    Task<ServiceResult> GetUnreadMessagesAsync(bool useCache = true);
    Task<ServiceResult> MarkMessageAsReadAsync(string messageId);
    Task MarkAllMessagesAsReadAsync();
    Task<int> CleanupOldMessagesAsync(int retentionDays = 30);
    Task UpdateLastSeenAsync(bool force = false);
    void StartListening();
    void StopListening();
    void InvalidateCache();
}
