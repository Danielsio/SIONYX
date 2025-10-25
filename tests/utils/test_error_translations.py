"""
Tests for error_translations utility
"""

from src.utils.error_translations import translate_error


class TestErrorTranslations:
    """Test cases for error translation functionality"""

    def test_translate_error_exact_match(self):
        """Test exact error message translation"""
        result = translate_error("invalid credentials")
        assert result == "פרטי התחברות שגויים"

    def test_translate_error_case_insensitive(self):
        """Test case insensitive error translation"""
        result = translate_error("INVALID CREDENTIALS")
        assert result == "פרטי התחברות שגויים"

    def test_translate_error_with_whitespace(self):
        """Test error translation with leading/trailing whitespace"""
        result = translate_error("  invalid credentials  ")
        assert result == "פרטי התחברות שגויים"

    def test_translate_error_partial_match(self):
        """Test partial error message matching"""
        result = translate_error("The user provided invalid credentials")
        assert result == "פרטי התחברות שגויים"

    def test_translate_error_email_exists(self):
        """Test email exists error translation"""
        result = translate_error("EMAIL_EXISTS")
        assert result == "מספר הטלפון כבר רשום במערכת"

    def test_translate_error_weak_password(self):
        """Test weak password error translation"""
        result = translate_error("WEAK_PASSWORD")
        assert result == "הסיסמה חלשה מדי"

    def test_translate_error_password_too_short(self):
        """Test password too short error translation"""
        result = translate_error("password must be at least 6 characters")
        assert result == "הסיסמה חייבת להכיל לפחות 6 תווים"

    def test_translate_error_access_denied(self):
        """Test access denied error translation"""
        result = translate_error("access denied")
        assert result == "אין הרשאה"

    def test_translate_error_session_expired(self):
        """Test session expired error translation"""
        result = translate_error("session expired")
        assert result == "הפעלה פגה - התחבר שוב"

    def test_translate_error_user_data_not_found(self):
        """Test user data not found error translation"""
        result = translate_error("user data not found")
        assert result == "נתוני המשתמש לא נמצאו"

    def test_translate_error_operation_failed(self):
        """Test operation failed error translation"""
        result = translate_error("operation failed")
        assert result == "הפעולה נכשלה"

    def test_translate_error_unknown_error(self):
        """Test unknown error message handling"""
        result = translate_error("unknown error message")
        assert result == "שגיאה: unknown error message"

    def test_translate_error_empty_string(self):
        """Test empty error message handling"""
        result = translate_error("")
        assert result == "שגיאה לא ידועה"

    def test_translate_error_none(self):
        """Test None error message handling"""
        result = translate_error(None)
        assert result == "שגיאה לא ידועה"

    def test_translate_error_with_dashes(self):
        """Test error message with dashes"""
        result = translate_error("access-denied")
        assert result == "אין הרשאה"

    def test_translate_error_with_underscores(self):
        """Test error message with underscores"""
        result = translate_error("session_expired")
        assert result == "הפעלה פגה - התחבר שוב"

    def test_translate_error_firebase_errors(self):
        """Test Firebase-specific error translations"""
        firebase_errors = [
            ("EMAIL_EXISTS", "מספר הטלפון כבר רשום במערכת"),
            ("INVALID_PASSWORD", "פרטי התחברות שגויים"),
            ("EMAIL_NOT_FOUND", "פרטי התחברות שגויים"),
            ("INVALID_LOGIN_CREDENTIALS", "פרטי התחברות שגויים"),
            ("WEAK_PASSWORD", "הסיסמה חלשה מדי"),
            ("TOO_MANY_ATTEMPTS", "יותר מדי ניסיונות - נסה שוב מאוחר יותר"),
            ("USER_DISABLED", "החשבון הושבת"),
            ("INVALID_EMAIL", "פרטי התחברות שגויים"),
            ("MISSING_PASSWORD", "שדה חובה"),
            ("OPERATION_NOT_ALLOWED", "אין הרשאה"),
        ]

        for english_error, expected_hebrew in firebase_errors:
            result = translate_error(english_error)
            assert result == expected_hebrew, f"Failed for error: {english_error}"

    def test_translate_error_complex_messages(self):
        """Test complex error messages with multiple parts"""
        complex_errors = [
            ("The operation failed due to invalid credentials", "פרטי התחברות שגויים"),
            ("Access denied: insufficient permissions", "אין הרשאה"),
            ("Session has expired, please login again", "הפעלה פגה - התחבר שוב"),
            ("User data not found in database", "נתוני המשתמש לא נמצאו"),
        ]

        for complex_error, expected_hebrew in complex_errors:
            result = translate_error(complex_error)
            assert (
                result == expected_hebrew
            ), f"Failed for complex error: {complex_error}"

    def test_translate_error_priority_order(self):
        """Test that more specific errors are matched before general ones"""
        # "invalid credentials" should match before "invalid"
        result = translate_error("invalid credentials")
        assert result == "פרטי התחברות שגויים"

        # "invalid input" should match "invalid input" specifically
        result = translate_error("invalid input")
        assert (
            result == "פרטי התחברות שגויים"
        )  # This should match "invalid credentials" pattern

    def test_translate_error_unicode_handling(self):
        """Test Unicode error message handling"""
        unicode_error = "שגיאה בעברית"
        result = translate_error(unicode_error)
        assert result == f"שגיאה: {unicode_error}"

    def test_translate_error_special_characters(self):
        """Test error messages with special characters"""
        special_errors = [
            ("Error: 404 Not Found", "שגיאה: Error: 404 Not Found"),
            ("Error! Something went wrong.", "שגיאה: Error! Something went wrong."),
            ("Error@#$%^&*()", "שגיאה: Error@#$%^&*()"),
        ]

        for special_error, expected in special_errors:
            result = translate_error(special_error)
            assert result == expected
