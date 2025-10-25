"""
Error message translations for Hebrew UI
"""

# Common error message translations
ERROR_TRANSLATIONS = {
    # Authentication errors
    "invalid credentials": "טלפון או סיסמה שגויים",
    "invalid-credentials": "טלפון או סיסמה שגויים",
    "user not found": "משתמש לא נמצא",
    "user-not-found": "משתמש לא נמצא",
    "wrong password": "סיסמה שגויה",
    "wrong-password": "סיסמה שגויה",
    "account disabled": "החשבון מושבת",
    "account-disabled": "החשבון מושבת",
    "too many attempts": "יותר מדי ניסיונות התחברות",
    "too-many-attempts": "יותר מדי ניסיונות התחברות",
    # Network errors
    "network error": "שגיאת רשת - בדוק את החיבור לאינטרנט",
    "network-error": "שגיאת רשת - בדוק את החיבור לאינטרנט",
    "connection timeout": "החיבור פג תוקף - נסה שוב",
    "connection-timeout": "החיבור פג תוקף - נסה שוב",
    "server error": "שגיאת שרת - נסה שוב מאוחר יותר",
    "server-error": "שגיאת שרת - נסה שוב מאוחר יותר",
    # Database errors
    "database error": "שגיאת מסד נתונים",
    "database-error": "שגיאת מסד נתונים",
    "data not found": "הנתונים לא נמצאו",
    "data-not-found": "הנתונים לא נמצאו",
    # Validation errors
    "invalid input": "קלט לא תקין",
    "invalid-input": "קלט לא תקין",
    "required field": "שדה חובה",
    "required-field": "שדה חובה",
    "invalid format": "פורמט לא תקין",
    "invalid-format": "פורמט לא תקין",
    # General errors
    "unknown error": "שגיאה לא ידועה",
    "unknown-error": "שגיאה לא ידועה",
    "operation failed": "הפעולה נכשלה",
    "operation-failed": "הפעולה נכשלה",
    "access denied": "אין הרשאה",
    "access-denied": "אין הרשאה",
    "session expired": "הפעלה פגה - התחבר שוב",
    "session-expired": "הפעלה פגה - התחבר שוב",
    # Password validation
    "password must be at least 6 characters": "הסיסמה חייבת להכיל לפחות 6 תווים",
    "password-too-short": "הסיסמה קצרה מדי",
    "password too weak": "הסיסמה חלשה מדי",
    "password-too-weak": "הסיסמה חלשה מדי",
    # User data errors
    "user data not found": "נתוני המשתמש לא נמצאו",
    "user-data-not-found": "נתוני המשתמש לא נמצאו",
    # Email/Account errors
    "email already exists": "מספר הטלפון כבר רשום במערכת",
    "email-already-exists": "מספר הטלפון כבר רשום במערכת",
}


def translate_error(error_message: str) -> str:
    """
    Translate error message to Hebrew

    Args:
        error_message: Original error message (English)

    Returns:
        Translated error message in Hebrew, or original if no translation found
    """
    if not error_message:
        return "שגיאה לא ידועה"

    # Clean the error message
    error_lower = error_message.lower().strip()

    # Try exact match first
    if error_lower in ERROR_TRANSLATIONS:
        return ERROR_TRANSLATIONS[error_lower]

    # Try partial matches for common patterns
    for english_error, hebrew_translation in ERROR_TRANSLATIONS.items():
        if english_error in error_lower:
            return hebrew_translation

    # If no translation found, return a generic message
    return f"שגיאה: {error_message}"
