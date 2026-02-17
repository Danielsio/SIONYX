using System.Text.Json;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Services;

/// <summary>
/// Chat service: SSE-based real-time messaging with cache and debounced last-seen.
/// Replaces PyQt6 signals with C# events.
/// </summary>
public class ChatService : BaseService, IDisposable
{
    protected override string ServiceName => "ChatService";

    private string _userId;
    private SseListener? _streamListener;
    private DateTime? _lastSeenUpdateTime;
    private readonly int _lastSeenDebounceSeconds = 60;

    // Cache
    private List<Dictionary<string, object?>> _cachedMessages = new();
    private DateTime? _cacheTimestamp;

    // State
    public bool IsListening { get; private set; }

    // C# events replace PyQt signals
    public event Action<List<Dictionary<string, object?>>>? MessagesReceived;

    public ChatService(FirebaseClient firebase, string userId) : base(firebase)
    {
        _userId = userId;
        Logger.Information("Chat service initialized for user {UserId} (SSE mode)", userId);
    }

    /// <summary>Update userId for a new login session (singleton reuse).</summary>
    public void Reinitialize(string userId)
    {
        StopListening();
        InvalidateCache();
        _userId = userId;
        Logger.Information("Chat service re-initialized for user {UserId}", userId);
    }

    /// <summary>Get all unread messages for the current user.</summary>
    public async Task<ServiceResult> GetUnreadMessagesAsync(bool useCache = true)
    {
        if (useCache && IsListening && _cachedMessages.Count > 0)
            return Success(_cachedMessages);

        if (useCache && _cacheTimestamp.HasValue && (DateTime.Now - _cacheTimestamp.Value).TotalSeconds < 10)
            return Success(_cachedMessages);

        var result = await Firebase.DbGetAsync("messages");
        if (!result.Success) return Error(result.Error ?? "Failed to fetch messages");

        if (result.Data is JsonElement data && data.ValueKind == JsonValueKind.Object)
        {
            var messages = ExtractUserMessages(data);
            UpdateCache(messages);
            return Success(messages);
        }

        UpdateCache(new List<Dictionary<string, object?>>());
        return Success(_cachedMessages);
    }

    /// <summary>Mark a specific message as read.</summary>
    public async Task<ServiceResult> MarkMessageAsReadAsync(string messageId)
    {
        await Firebase.DbSetAsync($"messages/{messageId}/read", true);
        await Firebase.DbSetAsync($"messages/{messageId}/readAt", DateTimeOffset.UtcNow.ToUnixTimeMilliseconds());
        return Success();
    }

    /// <summary>Mark all unread messages as read.</summary>
    public async Task MarkAllMessagesAsReadAsync()
    {
        var result = await GetUnreadMessagesAsync();
        if (!result.IsSuccess) return;
        var messages = (List<Dictionary<string, object?>>)result.Data!;
        foreach (var msg in messages)
        {
            if (msg.TryGetValue("id", out var id) && id is string messageId)
                await MarkMessageAsReadAsync(messageId);
        }
    }

    /// <summary>Update user's last seen timestamp (debounced).</summary>
    public async Task UpdateLastSeenAsync(bool force = false)
    {
        var now = DateTime.Now;
        if (!force && _lastSeenUpdateTime.HasValue &&
            (now - _lastSeenUpdateTime.Value).TotalSeconds < _lastSeenDebounceSeconds)
            return;

        await Firebase.DbSetAsync($"users/{_userId}/lastSeen", DateTimeOffset.UtcNow.ToUnixTimeMilliseconds());
        _lastSeenUpdateTime = now;
    }

    /// <summary>Start SSE listener for real-time messages.</summary>
    public void StartListening()
    {
        if (IsListening) return;
        IsListening = true;

        _streamListener = Firebase.DbListen("messages", OnStreamEvent, OnStreamError);
        Logger.Information("Started SSE listener for messages");
    }

    /// <summary>Stop listening for messages.</summary>
    public void StopListening()
    {
        if (!IsListening) return;
        IsListening = false;

        _streamListener?.Stop();
        _streamListener = null;
        Logger.Information("Stopped SSE listener for messages");
    }

    /// <summary>Invalidate the message cache.</summary>
    public void InvalidateCache()
    {
        _cachedMessages.Clear();
        _cacheTimestamp = null;
    }

    public void Dispose()
    {
        StopListening();
        InvalidateCache();
        GC.SuppressFinalize(this);
    }

    // ==================== PRIVATE ====================

    private void OnStreamEvent(string eventType, JsonElement? data)
    {
        try
        {
            if (eventType == "keep-alive")
            {
                _ = UpdateLastSeenAsync();
                return;
            }
            if (eventType is "cancel" or "auth_revoked") return;
            if (eventType is not ("put" or "patch")) return;

            // Re-fetch full messages to ensure consistency
            _ = Task.Run(async () =>
            {
                var result = await GetUnreadMessagesAsync(useCache: false);
                if (result.IsSuccess)
                    MessagesReceived?.Invoke((List<Dictionary<string, object?>>)result.Data!);
                await UpdateLastSeenAsync();
            });
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error processing SSE event");
        }
    }

    private void OnStreamError(string error)
    {
        Logger.Error("SSE stream error: {Error}", error);
    }

    private List<Dictionary<string, object?>> ExtractUserMessages(JsonElement allMessages)
    {
        var messages = new List<Dictionary<string, object?>>();
        if (allMessages.ValueKind != JsonValueKind.Object) return messages;

        foreach (var prop in allMessages.EnumerateObject())
        {
            if (prop.Value.ValueKind != JsonValueKind.Object) continue;
            var toUser = prop.Value.TryGetProperty("toUserId", out var tu) ? tu.GetString() : null;
            var isRead = prop.Value.TryGetProperty("read", out var r) && r.GetBoolean();

            if (toUser == _userId && !isRead)
            {
                var msg = new Dictionary<string, object?> { ["id"] = prop.Name };
                foreach (var field in prop.Value.EnumerateObject())
                    msg[field.Name] = field.Value.ValueKind switch
                    {
                        JsonValueKind.String => field.Value.GetString(),
                        JsonValueKind.True => true,
                        JsonValueKind.False => false,
                        JsonValueKind.Number => field.Value.GetDouble(),
                        _ => field.Value.ToString(),
                    };
                messages.Add(msg);
            }
        }

        messages.Sort((a, b) =>
        {
            var ta = a.TryGetValue("timestamp", out var va) ? va?.ToString() ?? "" : "";
            var tb = b.TryGetValue("timestamp", out var vb) ? vb?.ToString() ?? "" : "";
            return string.Compare(ta, tb, StringComparison.Ordinal);
        });

        return messages;
    }

    private void UpdateCache(List<Dictionary<string, object?>> messages)
    {
        _cachedMessages = messages;
        _cacheTimestamp = DateTime.Now;
    }
}
