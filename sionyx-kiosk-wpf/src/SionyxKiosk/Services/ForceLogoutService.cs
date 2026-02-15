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

    /// <summary>Raised when a force-logout command is received.</summary>
    public event Action<string>? ForceLogout; // reason string

    public ForceLogoutService(FirebaseClient firebase)
    {
        _firebase = firebase;
    }

    public void StartListening(string userId)
    {
        _userId = userId;
        StopListening();

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
