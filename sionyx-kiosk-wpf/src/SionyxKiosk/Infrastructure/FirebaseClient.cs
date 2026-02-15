using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Serilog;

namespace SionyxKiosk.Infrastructure;

/// <summary>
/// Firebase REST API client for Authentication + Realtime Database + SSE streaming.
/// Registered as a singleton in the DI container.
/// </summary>
public sealed class FirebaseClient : IDisposable
{
    private static readonly ILogger Logger = Log.ForContext<FirebaseClient>();
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    private readonly HttpClient _http;
    private readonly string _apiKey;
    private readonly string _databaseUrl;
    private readonly string _authUrl;
    private readonly string _orgId;

    // Auth state
    private string? _idToken;
    private string? _refreshToken;
    private DateTime _tokenExpiry;
    private string? _userId;
    private readonly SemaphoreSlim _tokenLock = new(1, 1);

    public string? UserId => _userId;
    public string? RefreshToken => _refreshToken;
    public string OrgId => _orgId;
    public bool IsAuthenticated => _idToken != null && _userId != null;

    public FirebaseClient(FirebaseConfig config, HttpClient? httpClient = null)
    {
        _apiKey = config.ApiKey;
        _databaseUrl = config.DatabaseUrl.TrimEnd('/');
        _authUrl = config.AuthUrl;
        _orgId = config.OrgId;
        _http = httpClient ?? new HttpClient { Timeout = TimeSpan.FromSeconds(30) };

        Logger.Information("Firebase client initialized (org: {OrgId})", _orgId);
    }

    // ==================== AUTHENTICATION ====================

    public async Task<FirebaseResult> SignUpAsync(string email, string password)
    {
        var url = $"{_authUrl}:signUp?key={_apiKey}";
        var payload = new { email, password, returnSecureToken = true };

        try
        {
            var response = await PostJsonAsync(url, payload);
            StoreAuthData(response);
            Logger.Information("User signed up: {UserId}", _userId);
            return FirebaseResult.Ok(new { uid = _userId, idToken = _idToken, refreshToken = _refreshToken });
        }
        catch (Exception ex)
        {
            var msg = ParseFirebaseError(ex);
            Logger.Error(ex, "Sign up failed");
            return FirebaseResult.Fail(msg);
        }
    }

    public async Task<FirebaseResult> SignInAsync(string email, string password)
    {
        var url = $"{_authUrl}:signInWithPassword?key={_apiKey}";
        var payload = new { email, password, returnSecureToken = true };

        try
        {
            var response = await PostJsonAsync(url, payload);
            StoreAuthData(response);
            Logger.Information("User signed in: {UserId}", _userId);
            return FirebaseResult.Ok(new { uid = _userId, idToken = _idToken, refreshToken = _refreshToken });
        }
        catch (Exception ex)
        {
            var msg = ParseFirebaseError(ex);
            Logger.Error(ex, "Sign in failed");
            return FirebaseResult.Fail(msg);
        }
    }

    public async Task<bool> RefreshTokenAsync()
    {
        if (string.IsNullOrEmpty(_refreshToken)) return false;

        var url = $"https://securetoken.googleapis.com/v1/token?key={_apiKey}";
        var payload = new { grant_type = "refresh_token", refresh_token = _refreshToken };

        try
        {
            var response = await PostJsonAsync(url, payload);
            _idToken = GetString(response, "id_token");
            _refreshToken = GetString(response, "refresh_token");
            _userId = GetString(response, "user_id");
            var expiresIn = int.Parse(GetString(response, "expires_in") ?? "3600");
            _tokenExpiry = DateTime.UtcNow.AddSeconds(expiresIn);

            Logger.Information("Token refreshed successfully");
            return true;
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "Token refresh failed");
            return false;
        }
    }

    /// <summary>Ensure the auth token is valid, refreshing if needed.</summary>
    public async Task<bool> EnsureValidTokenAsync()
    {
        if (_idToken == null || _refreshToken == null) return false;

        // Refresh if expiring within 5 minutes
        if (DateTime.UtcNow >= _tokenExpiry.AddMinutes(-5))
        {
            await _tokenLock.WaitAsync();
            try
            {
                // Double-check after acquiring lock
                if (DateTime.UtcNow >= _tokenExpiry.AddMinutes(-5))
                    return await RefreshTokenAsync();
            }
            finally
            {
                _tokenLock.Release();
            }
        }

        return true;
    }

    /// <summary>Clear auth state on logout.</summary>
    public void ClearAuth()
    {
        _idToken = null;
        _refreshToken = null;
        _userId = null;
        _tokenExpiry = DateTime.MinValue;
        Logger.Information("Auth state cleared");
    }

    /// <summary>Restore auth state from saved tokens (e.g., local DB).</summary>
    public void RestoreAuth(string idToken, string refreshToken, string userId)
    {
        _idToken = idToken;
        _refreshToken = refreshToken;
        _userId = userId;
        _tokenExpiry = DateTime.UtcNow.AddMinutes(30); // Will refresh if needed
    }

    // ==================== REALTIME DATABASE ====================

    private string GetOrgPath(string path) =>
        $"organizations/{_orgId}/{path.Trim('/')}";

    public async Task<FirebaseResult> DbGetAsync(string path)
    {
        if (!await EnsureValidTokenAsync())
            return FirebaseResult.Fail("Not authenticated");

        var orgPath = GetOrgPath(path);
        var url = $"{_databaseUrl}/{orgPath}.json?auth={_idToken}";

        try
        {
            var response = await _http.GetAsync(url);
            response.EnsureSuccessStatusCode();
            var json = await response.Content.ReadAsStringAsync();
            var data = JsonSerializer.Deserialize<JsonElement>(json);
            Logger.Debug("DB read: {Path}", orgPath);
            return FirebaseResult.Ok(data);
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "DB read failed: {Path}", orgPath);
            return FirebaseResult.Fail(ex.Message);
        }
    }

    public async Task<FirebaseResult> DbSetAsync(string path, object data)
    {
        if (!await EnsureValidTokenAsync())
            return FirebaseResult.Fail("Not authenticated");

        var orgPath = GetOrgPath(path);
        var url = $"{_databaseUrl}/{orgPath}.json?auth={_idToken}";
        var content = new StringContent(JsonSerializer.Serialize(data, JsonOptions), Encoding.UTF8, "application/json");

        try
        {
            var response = await _http.PutAsync(url, content);
            response.EnsureSuccessStatusCode();
            Logger.Debug("DB write: {Path}", orgPath);
            return FirebaseResult.Ok();
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "DB write failed: {Path}", orgPath);
            return FirebaseResult.Fail(ex.Message);
        }
    }

    public async Task<FirebaseResult> DbUpdateAsync(string path, object data)
    {
        if (!await EnsureValidTokenAsync())
            return FirebaseResult.Fail("Not authenticated");

        var orgPath = GetOrgPath(path);
        var url = $"{_databaseUrl}/{orgPath}.json?auth={_idToken}";
        var content = new StringContent(JsonSerializer.Serialize(data, JsonOptions), Encoding.UTF8, "application/json");

        try
        {
            var request = new HttpRequestMessage(HttpMethod.Patch, url) { Content = content };
            var response = await _http.SendAsync(request);
            response.EnsureSuccessStatusCode();
            Logger.Debug("DB update: {Path}", orgPath);
            return FirebaseResult.Ok();
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "DB update failed: {Path}", orgPath);
            return FirebaseResult.Fail(ex.Message);
        }
    }

    public async Task<FirebaseResult> DbDeleteAsync(string path)
    {
        if (!await EnsureValidTokenAsync())
            return FirebaseResult.Fail("Not authenticated");

        var orgPath = GetOrgPath(path);
        var url = $"{_databaseUrl}/{orgPath}.json?auth={_idToken}";

        try
        {
            var response = await _http.DeleteAsync(url);
            response.EnsureSuccessStatusCode();
            Logger.Debug("DB delete: {Path}", orgPath);
            return FirebaseResult.Ok();
        }
        catch (Exception ex)
        {
            Logger.Error(ex, "DB delete failed: {Path}", orgPath);
            return FirebaseResult.Fail(ex.Message);
        }
    }

    // ==================== SSE STREAMING ====================

    /// <summary>
    /// Listen to real-time changes on a database path using Server-Sent Events.
    /// Returns a SseListener that can be stopped via its CancellationTokenSource.
    /// </summary>
    public SseListener DbListen(string path, Action<string, JsonElement?> callback, Action<string>? errorCallback = null)
    {
        var listener = new SseListener(this, path, callback, errorCallback);
        listener.Start();
        return listener;
    }

    // Expose internals needed by SseListener
    internal string DatabaseUrl => _databaseUrl;
    internal string? IdToken => _idToken;
    internal string GetOrgPathInternal(string path) => GetOrgPath(path);
    internal HttpClient Http => _http;

    // ==================== HELPERS ====================

    private async Task<Dictionary<string, JsonElement>> PostJsonAsync(string url, object payload)
    {
        var json = JsonSerializer.Serialize(payload, JsonOptions);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        var response = await _http.PostAsync(url, content);

        var responseBody = await response.Content.ReadAsStringAsync();

        if (!response.IsSuccessStatusCode)
        {
            // Throw with the response body so ParseFirebaseError can parse it
            throw new FirebaseApiException(response.StatusCode, responseBody);
        }

        return JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(responseBody) ?? [];
    }

    private void StoreAuthData(Dictionary<string, JsonElement> data)
    {
        _idToken = GetString(data, "idToken");
        _refreshToken = GetString(data, "refreshToken");
        _userId = GetString(data, "localId");
        var expiresIn = int.Parse(GetString(data, "expiresIn") ?? "3600");
        _tokenExpiry = DateTime.UtcNow.AddSeconds(expiresIn);
    }

    private static string? GetString(Dictionary<string, JsonElement> data, string key) =>
        data.TryGetValue(key, out var element) ? element.GetString() ?? element.ToString() : null;

    private static string ParseFirebaseError(Exception ex)
    {
        if (ex is FirebaseApiException apiEx)
        {
            try
            {
                var errorDoc = JsonDocument.Parse(apiEx.ResponseBody);
                var message = errorDoc.RootElement
                    .GetProperty("error")
                    .GetProperty("message")
                    .GetString() ?? "";

                return message switch
                {
                    var m when m.Contains("EMAIL_EXISTS") => ErrorTranslations.Translate("email already exists"),
                    var m when m.Contains("INVALID_PASSWORD") || m.Contains("EMAIL_NOT_FOUND") => ErrorTranslations.Translate("invalid credentials"),
                    var m when m.Contains("INVALID_LOGIN_CREDENTIALS") => ErrorTranslations.Translate("invalid credentials"),
                    var m when m.Contains("WEAK_PASSWORD") => ErrorTranslations.Translate("password too weak"),
                    var m when m.Contains("TOO_MANY_ATTEMPTS") => ErrorTranslations.Translate("too many attempts"),
                    var m when m.Contains("USER_DISABLED") => ErrorTranslations.Translate("account disabled"),
                    var m when m.Contains("INVALID_EMAIL") => ErrorTranslations.Translate("invalid input"),
                    var m when m.Contains("MISSING_PASSWORD") => ErrorTranslations.Translate("required field"),
                    _ => ErrorTranslations.Translate(message),
                };
            }
            catch
            {
                // Fall through
            }
        }

        return ErrorTranslations.Translate(ex.Message);
    }

    public void Dispose()
    {
        _tokenLock.Dispose();
        _http.Dispose();
    }
}

/// <summary>Typed result from Firebase operations.</summary>
public class FirebaseResult
{
    public bool Success { get; init; }
    public string? Error { get; init; }
    public object? Data { get; init; }

    public static FirebaseResult Ok(object? data = null) => new() { Success = true, Data = data };
    public static FirebaseResult Fail(string error) => new() { Success = false, Error = error };
}

/// <summary>Exception with HTTP status and response body from Firebase API.</summary>
public class FirebaseApiException : Exception
{
    public System.Net.HttpStatusCode StatusCode { get; }
    public string ResponseBody { get; }

    public FirebaseApiException(System.Net.HttpStatusCode statusCode, string responseBody)
        : base($"Firebase API error ({statusCode}): {responseBody}")
    {
        StatusCode = statusCode;
        ResponseBody = responseBody;
    }
}
