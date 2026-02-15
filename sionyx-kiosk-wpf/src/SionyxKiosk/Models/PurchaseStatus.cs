namespace SionyxKiosk.Models;

/// <summary>
/// Purchase status values stored in Firebase.
/// </summary>
public enum PurchaseStatus
{
    Pending,
    Completed,
    Failed
}

/// <summary>
/// Extension methods for PurchaseStatus - Hebrew labels, colors, Nedarim mapping.
/// </summary>
public static class PurchaseStatusExtensions
{
    /// <summary>Firebase database string value.</summary>
    public static string ToDbValue(this PurchaseStatus status) => status switch
    {
        PurchaseStatus.Pending => "pending",
        PurchaseStatus.Completed => "completed",
        PurchaseStatus.Failed => "failed",
        _ => "pending"
    };

    /// <summary>Hebrew display label for UI.</summary>
    public static string ToHebrewLabel(this PurchaseStatus status) => status switch
    {
        PurchaseStatus.Pending => "ממתין",
        PurchaseStatus.Completed => "הושלם",
        PurchaseStatus.Failed => "נכשל",
        _ => status.ToString()
    };

    /// <summary>Semantic color name for UI badges.</summary>
    public static string ToColorName(this PurchaseStatus status) => status switch
    {
        PurchaseStatus.Pending => "processing",
        PurchaseStatus.Completed => "success",
        PurchaseStatus.Failed => "error",
        _ => "default"
    };

    /// <summary>Whether this status is final (no further transitions).</summary>
    public static bool IsFinal(this PurchaseStatus status) =>
        status is PurchaseStatus.Completed or PurchaseStatus.Failed;

    /// <summary>Parse a database string value to PurchaseStatus.</summary>
    public static PurchaseStatus Parse(string? dbValue) => dbValue?.ToLowerInvariant() switch
    {
        "completed" => PurchaseStatus.Completed,
        "failed" => PurchaseStatus.Failed,
        "pending" => PurchaseStatus.Pending,
        _ => PurchaseStatus.Pending
    };

    /// <summary>Map Nedarim payment gateway response to PurchaseStatus.</summary>
    public static PurchaseStatus FromNedarimStatus(string? nedarimStatus) =>
        nedarimStatus == "Error" ? PurchaseStatus.Failed : PurchaseStatus.Completed;
}
