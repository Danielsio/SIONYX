using System.Text.Json;
using Serilog;
using SionyxKiosk.Infrastructure;

namespace SionyxKiosk.Services;

/// <summary>
/// Abstract base class for all services. Provides shared error handling,
/// response formatting, auth checks, and Firebase access.
/// </summary>
public abstract class BaseService
{
    protected readonly FirebaseClient Firebase;
    protected readonly ILogger Logger;

    protected BaseService(FirebaseClient firebase)
    {
        Firebase = firebase;
        Logger = Log.ForContext(GetType());
    }

    /// <summary>Service name for logging.</summary>
    protected abstract string ServiceName { get; }

    // ==================== RESPONSE HELPERS ====================

    protected static ServiceResult Success(object? data = null, string? message = null) =>
        new() { IsSuccess = true, Data = data, Message = message };

    protected static ServiceResult Error(string error, string? errorCode = null) =>
        new() { IsSuccess = false, Error = error, ErrorCode = errorCode };

    // ==================== AUTH CHECKS ====================

    protected bool IsAuthenticated() => Firebase.IsAuthenticated;

    protected ServiceResult RequireAuthentication()
    {
        if (!IsAuthenticated())
            return Error("Not authenticated", "AUTH_REQUIRED");
        return Success();
    }

    // ==================== SAFE HELPERS ====================

    protected static string SafeGet(JsonElement element, string property, string defaultValue = "")
    {
        if (element.ValueKind == JsonValueKind.Object &&
            element.TryGetProperty(property, out var prop))
        {
            return prop.GetString() ?? defaultValue;
        }
        return defaultValue;
    }

    protected static int SafeGetInt(JsonElement element, string property, int defaultValue = 0)
    {
        if (element.ValueKind == JsonValueKind.Object &&
            element.TryGetProperty(property, out var prop))
        {
            if (prop.ValueKind == JsonValueKind.Number && prop.TryGetInt32(out var val))
                return val;
            if (prop.ValueKind == JsonValueKind.String && int.TryParse(prop.GetString(), out var parsed))
                return parsed;
        }
        return defaultValue;
    }

    protected static double SafeGetDouble(JsonElement element, string property, double defaultValue = 0.0)
    {
        if (element.ValueKind == JsonValueKind.Object &&
            element.TryGetProperty(property, out var prop))
        {
            if (prop.ValueKind == JsonValueKind.Number && prop.TryGetDouble(out var val))
                return val;
            if (prop.ValueKind == JsonValueKind.String && double.TryParse(prop.GetString(), out var parsed))
                return parsed;
        }
        return defaultValue;
    }

    // ==================== FIREBASE ERROR HANDLING ====================

    protected string HandleFirebaseError(Exception ex, string operation)
    {
        var errorMsg = ErrorTranslations.Translate(ex.Message);
        Logger.Error(ex, "{Service}.{Operation} failed: {Error}", ServiceName, operation, errorMsg);
        return errorMsg;
    }

    protected void LogOperation(string operation, string? details = null)
    {
        if (details != null)
            Logger.Debug("{Service}.{Operation}: {Details}", ServiceName, operation, details);
        else
            Logger.Debug("{Service}.{Operation}", ServiceName, operation);
    }
}

/// <summary>
/// Standardized service response.
/// </summary>
public class ServiceResult
{
    public bool IsSuccess { get; init; }
    public string? Error { get; init; }
    public string? ErrorCode { get; init; }
    public string? Message { get; init; }
    public object? Data { get; init; }

    /// <summary>Get typed data from the result.</summary>
    public T? GetData<T>() where T : class => Data as T;
}
