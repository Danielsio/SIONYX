using System.Text.Json;
using Serilog;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Services;

/// <summary>
/// Listens for force-logout commands from Firebase via SSE.
/// When an admin forces a user off, this triggers the ForceLogout event.
/// </summary>
public class ForceLogoutService
{
    private static readonly ILogger Log = Serilog.Log.ForContext<ForceLogoutService>();
    private readonly FirebaseClient _firebase;
    private SseListener? _listener;
    private string? _userId;
    private bool _isFirstEvent;

    /// <summary>Raised when a force-logout command is received.</summary>
    public event Action<string>? ForceLogout; // reason string

    public ForceLogoutService(FirebaseClient firebase)
    {
        _firebase = firebase;
    }

    public async void StartListening(string userId)
    {
        _userId = userId;
        StopListening();

        // Clear any stale force-logout data BEFORE connecting SSE
        try
        {
            await _firebase.DbDeleteAsync($"users/{userId}/forceLogout");
            Log.Debug("ForceLogoutService: cleared stale force-logout data");
        }
        catch (Exception ex)
        {
            Log.Debug(ex, "ForceLogoutService: could not clear stale data (non-fatal)");
        }

        _isFirstEvent = true;
        var path = $"users/{userId}/forceLogout";
        _listener = _firebase.DbListen(path, OnEvent);
        Log.Information("ForceLogoutService: listening on {Path}", path);
    }

    public void StopListening()
    {
        _listener?.Stop();
        _listener = null;
    }

    private void OnEvent(string eventType, JsonElement? data)
    {
        if (eventType != "put" || data == null) return;

        try
        {
            // The first SSE event is always the current state — skip it.
            // We already cleared stale data in StartListening, but if the
            // delete failed the initial event would still carry old data.
            if (_isFirstEvent)
            {
                _isFirstEvent = false;
                if (data.Value.ValueKind != JsonValueKind.Null)
                {
                    Log.Debug("ForceLogoutService: ignoring initial SSE state (stale data)");
                    _ = _firebase.DbDeleteAsync($"users/{_userId}/forceLogout");
                }
                return;
            }

            if (data.Value.ValueKind == JsonValueKind.Null) return;

            var reason = "admin_forced";
            if (data.Value.TryGetProperty("reason", out var r))
                reason = r.GetString() ?? reason;

            Log.Warning("ForceLogoutService: received force-logout, reason={Reason}", reason);
            ForceLogout?.Invoke(reason);

            // Clear the force-logout flag
            _ = _firebase.DbDeleteAsync($"users/{_userId}/forceLogout");
        }
        catch (Exception ex)
        {
            Log.Error(ex, "ForceLogoutService: error processing event");
        }
    }
}
