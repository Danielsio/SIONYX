using System.IO;
using System.Net.Http;
using System.Text.Json;
using Serilog;

namespace SionyxKiosk.Infrastructure;

/// <summary>
/// Server-Sent Events (SSE) listener for Firebase Realtime Database.
/// Maintains a persistent connection with auto-reconnect and exponential backoff.
/// </summary>
public sealed class SseListener
{
    private static readonly ILogger Logger = Log.ForContext<SseListener>();

    private readonly FirebaseClient _firebase;
    private readonly string _path;
    private readonly Action<string, JsonElement?> _callback;
    private readonly Action<string>? _errorCallback;

    private CancellationTokenSource? _cts;
    private Task? _listenTask;
    private int _reconnectDelay = 1;
    private const int MaxReconnectDelay = 60;

    public bool IsRunning => _cts != null && !_cts.IsCancellationRequested;

    internal SseListener(
        FirebaseClient firebase,
        string path,
        Action<string, JsonElement?> callback,
        Action<string>? errorCallback)
    {
        _firebase = firebase;
        _path = path;
        _callback = callback;
        _errorCallback = errorCallback;
    }

    /// <summary>Start listening in a background task.</summary>
    internal void Start()
    {
        if (IsRunning)
        {
            Logger.Warning("SSE listener already running for {Path}", _path);
            return;
        }

        _cts = new CancellationTokenSource();
        _listenTask = Task.Run(() => ListenLoopAsync(_cts.Token), _cts.Token);
        Logger.Information("SSE listener started for: {Path}", _path);
    }

    /// <summary>Stop the listener gracefully.</summary>
    public void Stop()
    {
        Logger.Debug("Stopping SSE listener for: {Path}", _path);
        _cts?.Cancel();

        // Wait briefly for clean shutdown
        try
        {
            _listenTask?.Wait(TimeSpan.FromMilliseconds(500));
        }
        catch (AggregateException)
        {
            // Expected on cancellation
        }

        _cts?.Dispose();
        _cts = null;
        Logger.Information("SSE listener stopped for: {Path}", _path);
    }

    private async Task ListenLoopAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            try
            {
                await ConnectAndStreamAsync(ct);
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (Exception ex)
            {
                if (ct.IsCancellationRequested) break;

                Logger.Error(ex, "SSE connection error for {Path}", _path);
                _errorCallback?.Invoke(ex.Message);

                // Exponential backoff
                Logger.Information("SSE reconnecting in {Delay}s for {Path}", _reconnectDelay, _path);
                try
                {
                    await Task.Delay(TimeSpan.FromSeconds(_reconnectDelay), ct);
                }
                catch (OperationCanceledException)
                {
                    break;
                }

                _reconnectDelay = Math.Min(_reconnectDelay * 2, MaxReconnectDelay);
            }
        }
    }

    private async Task ConnectAndStreamAsync(CancellationToken ct)
    {
        if (!await _firebase.EnsureValidTokenAsync())
            throw new InvalidOperationException("Not authenticated");

        var orgPath = _firebase.GetOrgPathInternal(_path);
        var url = $"{_firebase.DatabaseUrl}/{orgPath}.json?auth={_firebase.IdToken}";

        using var request = new HttpRequestMessage(HttpMethod.Get, url);
        request.Headers.Accept.Add(new System.Net.Http.Headers.MediaTypeWithQualityHeaderValue("text/event-stream"));
        request.Headers.CacheControl = new System.Net.Http.Headers.CacheControlHeaderValue { NoCache = true };

        using var response = await _firebase.Http.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, ct);
        response.EnsureSuccessStatusCode();

        _reconnectDelay = 1; // Reset backoff on successful connection
        Logger.Information("SSE stream connected: {Path}", orgPath);

        using var stream = await response.Content.ReadAsStreamAsync(ct);
        using var reader = new StreamReader(stream);

        string? eventType = null;
        var dataLines = new List<string>();

        while (!ct.IsCancellationRequested)
        {
            var line = await reader.ReadLineAsync(ct);
            if (line == null) break; // Stream closed

            if (line.StartsWith("event:"))
            {
                eventType = line[6..].Trim();
            }
            else if (line.StartsWith("data:"))
            {
                dataLines.Add(line[5..].Trim());
            }
            else if (line == "" && eventType != null)
            {
                // Empty line = end of event
                ProcessEvent(eventType, string.Join("", dataLines));
                eventType = null;
                dataLines.Clear();
            }
        }
    }

    private void ProcessEvent(string eventType, string dataStr)
    {
        try
        {
            switch (eventType)
            {
                case "keep-alive":
                    Logger.Debug("SSE keep-alive received");
                    return;
                case "cancel":
                    Logger.Warning("SSE stream cancelled by server");
                    _callback(eventType, null);
                    return;
                case "auth_revoked":
                    Logger.Warning("SSE auth revoked");
                    _callback(eventType, null);
                    return;
            }

            if (!string.IsNullOrEmpty(dataStr))
            {
                var data = JsonSerializer.Deserialize<JsonElement>(dataStr);
                _callback(eventType, data);
            }
            else
            {
                _callback(eventType, null);
            }
        }
        catch (JsonException ex)
        {
            Logger.Error(ex, "Failed to parse SSE data: {Raw}", dataStr[..Math.Min(dataStr.Length, 100)]);
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Error processing SSE event");
        }
    }
}
