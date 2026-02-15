namespace SionyxKiosk.Infrastructure;

/// <summary>
/// Maps English error messages to Hebrew for the UI.
/// </summary>
public static class ErrorTranslations
{
    private static readonly Dictionary<string, string> Translations = new(StringComparer.OrdinalIgnoreCase)
    {
        // Authentication errors
        ["invalid credentials"] = "טלפון או סיסמה שגויים",
        ["invalid-credentials"] = "טלפון או סיסמה שגויים",
        ["user not found"] = "משתמש לא נמצא",
        ["user-not-found"] = "משתמש לא נמצא",
        ["wrong password"] = "סיסמה שגויה",
        ["wrong-password"] = "סיסמה שגויה",
        ["account disabled"] = "החשבון מושבת",
        ["account-disabled"] = "החשבון מושבת",
        ["too many attempts"] = "יותר מדי ניסיונות התחברות",
        ["too-many-attempts"] = "יותר מדי ניסיונות התחברות",

        // Network errors
        ["network error"] = "שגיאת רשת - בדוק את החיבור לאינטרנט",
        ["network-error"] = "שגיאת רשת - בדוק את החיבור לאינטרנט",
        ["connection timeout"] = "החיבור פג תוקף - נסה שוב",
        ["connection-timeout"] = "החיבור פג תוקף - נסה שוב",
        ["server error"] = "שגיאת שרת - נסה שוב מאוחר יותר",
        ["server-error"] = "שגיאת שרת - נסה שוב מאוחר יותר",

        // Database errors
        ["database error"] = "שגיאת מסד נתונים",
        ["database-error"] = "שגיאת מסד נתונים",
        ["data not found"] = "הנתונים לא נמצאו",
        ["data-not-found"] = "הנתונים לא נמצאו",

        // Validation errors
        ["invalid input"] = "קלט לא תקין",
        ["invalid-input"] = "קלט לא תקין",
        ["required field"] = "שדה חובה",
        ["required-field"] = "שדה חובה",
        ["invalid format"] = "פורמט לא תקין",
        ["invalid-format"] = "פורמט לא תקין",

        // General errors
        ["unknown error"] = "שגיאה לא ידועה",
        ["unknown-error"] = "שגיאה לא ידועה",
        ["operation failed"] = "הפעולה נכשלה",
        ["operation-failed"] = "הפעולה נכשלה",
        ["access denied"] = "אין הרשאה",
        ["access-denied"] = "אין הרשאה",
        ["session expired"] = "הפעלה פגה - התחבר שוב",
        ["session-expired"] = "הפעלה פגה - התחבר שוב",

        // Password validation
        ["password must be at least 6 characters"] = "הסיסמה חייבת להכיל לפחות 6 תווים",
        ["password-too-short"] = "הסיסמה קצרה מדי",
        ["password too weak"] = "הסיסמה חלשה מדי",
        ["password-too-weak"] = "הסיסמה חלשה מדי",

        // User data errors
        ["user data not found"] = "נתוני המשתמש לא נמצאו",
        ["user-data-not-found"] = "נתוני המשתמש לא נמצאו",

        // Email/Account errors
        ["email already exists"] = "מספר הטלפון כבר רשום במערכת",
        ["email-already-exists"] = "מספר הטלפון כבר רשום במערכת",
    };

    /// <summary>
    /// Translate an error message to Hebrew.
    /// Returns the original message prefixed with "שגיאה:" if no translation is found.
    /// </summary>
    public static string Translate(string? errorMessage)
    {
        if (string.IsNullOrWhiteSpace(errorMessage))
            return "שגיאה לא ידועה";

        var trimmed = errorMessage.Trim();

        // Exact match (case-insensitive via comparer)
        if (Translations.TryGetValue(trimmed, out var translation))
            return translation;

        // Partial match: check if any known key is contained in the message
        var lower = trimmed.ToLowerInvariant();
        foreach (var kvp in Translations)
        {
            if (lower.Contains(kvp.Key, StringComparison.OrdinalIgnoreCase))
                return kvp.Value;
        }

        return $"שגיאה: {errorMessage}";
    }
}
