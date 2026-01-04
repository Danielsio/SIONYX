"""
Tests for error_translations.py - Error message translations
Tests translation of error messages to Hebrew.
"""

import pytest

from utils.error_translations import (
    ERROR_TRANSLATIONS,
    translate_error,
)


# =============================================================================
# ERROR_TRANSLATIONS dictionary tests
# =============================================================================
class TestErrorTranslations:
    """Tests for ERROR_TRANSLATIONS dictionary"""

    def test_dictionary_not_empty(self):
        """Test dictionary is not empty"""
        assert len(ERROR_TRANSLATIONS) > 0

    def test_contains_authentication_errors(self):
        """Test dictionary contains auth errors"""
        assert "invalid credentials" in ERROR_TRANSLATIONS
        assert "user not found" in ERROR_TRANSLATIONS

    def test_contains_network_errors(self):
        """Test dictionary contains network errors"""
        assert "network error" in ERROR_TRANSLATIONS
        assert "connection timeout" in ERROR_TRANSLATIONS

    def test_contains_database_errors(self):
        """Test dictionary contains database errors"""
        assert "database error" in ERROR_TRANSLATIONS
        assert "data not found" in ERROR_TRANSLATIONS

    def test_contains_validation_errors(self):
        """Test dictionary contains validation errors"""
        assert "invalid input" in ERROR_TRANSLATIONS
        assert "required field" in ERROR_TRANSLATIONS

    def test_contains_password_errors(self):
        """Test dictionary contains password errors"""
        assert "password too weak" in ERROR_TRANSLATIONS

    def test_translations_are_hebrew(self):
        """Test translations are in Hebrew"""
        # Check for Hebrew characters in translations
        for translation in ERROR_TRANSLATIONS.values():
            # Hebrew characters are in range 0x0590-0x05FF
            has_hebrew = any('\u0590' <= char <= '\u05FF' for char in translation)
            assert has_hebrew, f"Translation not in Hebrew: {translation}"


# =============================================================================
# translate_error function tests
# =============================================================================
class TestTranslateError:
    """Tests for translate_error function"""

    def test_exact_match_lowercase(self):
        """Test exact match translation"""
        result = translate_error("invalid credentials")
        assert result == "טלפון או סיסמה שגויים"

    def test_exact_match_with_dashes(self):
        """Test exact match with dashes"""
        result = translate_error("user-not-found")
        assert result == "משתמש לא נמצא"

    def test_case_insensitive(self):
        """Test translation is case insensitive"""
        result = translate_error("INVALID CREDENTIALS")
        assert result == "טלפון או סיסמה שגויים"

    def test_mixed_case(self):
        """Test mixed case input"""
        result = translate_error("Invalid Credentials")
        assert result == "טלפון או סיסמה שגויים"

    def test_partial_match(self):
        """Test partial match in longer message"""
        result = translate_error("Error: user not found in database")
        assert result == "משתמש לא נמצא"

    def test_unknown_error_returns_original(self):
        """Test unknown error returns original with prefix"""
        result = translate_error("some random error")
        assert "שגיאה:" in result
        assert "some random error" in result

    def test_empty_string_returns_default(self):
        """Test empty string returns default"""
        result = translate_error("")
        assert result == "שגיאה לא ידועה"

    def test_none_returns_default(self):
        """Test None returns default"""
        result = translate_error(None)
        assert result == "שגיאה לא ידועה"

    def test_whitespace_handling(self):
        """Test whitespace is stripped"""
        result = translate_error("  network error  ")
        assert result == "שגיאת רשת - בדוק את החיבור לאינטרנט"

    def test_wrong_password(self):
        """Test wrong password translation"""
        result = translate_error("wrong password")
        assert result == "סיסמה שגויה"

    def test_account_disabled(self):
        """Test account disabled translation"""
        result = translate_error("account disabled")
        assert result == "החשבון מושבת"

    def test_too_many_attempts(self):
        """Test too many attempts translation"""
        result = translate_error("too many attempts")
        assert result == "יותר מדי ניסיונות התחברות"

    def test_server_error(self):
        """Test server error translation"""
        result = translate_error("server error")
        assert result == "שגיאת שרת - נסה שוב מאוחר יותר"

    def test_access_denied(self):
        """Test access denied translation"""
        result = translate_error("access denied")
        assert result == "אין הרשאה"

    def test_session_expired(self):
        """Test session expired translation"""
        result = translate_error("session expired")
        assert result == "הפעלה פגה - התחבר שוב"

    def test_email_already_exists(self):
        """Test email already exists translation"""
        result = translate_error("email already exists")
        assert result == "מספר הטלפון כבר רשום במערכת"

    def test_password_too_short(self):
        """Test password validation error"""
        result = translate_error("password must be at least 6 characters")
        assert result == "הסיסמה חייבת להכיל לפחות 6 תווים"







