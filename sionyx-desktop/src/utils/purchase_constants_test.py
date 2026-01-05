"""
Tests for purchase_constants.py - Purchase status constants
Tests status values, labels, colors, and helper functions.
"""

import pytest

from utils.purchase_constants import (
    PURCHASE_STATUS,
    PURCHASE_STATUS_COLORS,
    PURCHASE_STATUS_LABELS,
    get_status_color,
    get_status_from_nedarim,
    get_status_label,
    is_final_status,
)


# =============================================================================
# PURCHASE_STATUS dictionary tests
# =============================================================================
class TestPurchaseStatus:
    """Tests for PURCHASE_STATUS dictionary"""

    def test_has_pending_status(self):
        """Test dictionary has PENDING status"""
        assert "PENDING" in PURCHASE_STATUS
        assert PURCHASE_STATUS["PENDING"] == "pending"

    def test_has_completed_status(self):
        """Test dictionary has COMPLETED status"""
        assert "COMPLETED" in PURCHASE_STATUS
        assert PURCHASE_STATUS["COMPLETED"] == "completed"

    def test_has_failed_status(self):
        """Test dictionary has FAILED status"""
        assert "FAILED" in PURCHASE_STATUS
        assert PURCHASE_STATUS["FAILED"] == "failed"

    def test_values_are_lowercase(self):
        """Test all values are lowercase"""
        for value in PURCHASE_STATUS.values():
            assert value == value.lower()


# =============================================================================
# PURCHASE_STATUS_LABELS dictionary tests
# =============================================================================
class TestPurchaseStatusLabels:
    """Tests for PURCHASE_STATUS_LABELS dictionary"""

    def test_has_label_for_pending(self):
        """Test has Hebrew label for pending"""
        assert PURCHASE_STATUS["PENDING"] in PURCHASE_STATUS_LABELS
        assert PURCHASE_STATUS_LABELS["pending"] == "ממתין"

    def test_has_label_for_completed(self):
        """Test has Hebrew label for completed"""
        assert PURCHASE_STATUS["COMPLETED"] in PURCHASE_STATUS_LABELS
        assert PURCHASE_STATUS_LABELS["completed"] == "הושלם"

    def test_has_label_for_failed(self):
        """Test has Hebrew label for failed"""
        assert PURCHASE_STATUS["FAILED"] in PURCHASE_STATUS_LABELS
        assert PURCHASE_STATUS_LABELS["failed"] == "נכשל"

    def test_labels_are_hebrew(self):
        """Test labels are in Hebrew"""
        for label in PURCHASE_STATUS_LABELS.values():
            has_hebrew = any("\u0590" <= char <= "\u05ff" for char in label)
            assert has_hebrew, f"Label not in Hebrew: {label}"


# =============================================================================
# PURCHASE_STATUS_COLORS dictionary tests
# =============================================================================
class TestPurchaseStatusColors:
    """Tests for PURCHASE_STATUS_COLORS dictionary"""

    def test_has_color_for_pending(self):
        """Test has color for pending"""
        assert PURCHASE_STATUS["PENDING"] in PURCHASE_STATUS_COLORS
        assert PURCHASE_STATUS_COLORS["pending"] == "processing"

    def test_has_color_for_completed(self):
        """Test has color for completed"""
        assert PURCHASE_STATUS["COMPLETED"] in PURCHASE_STATUS_COLORS
        assert PURCHASE_STATUS_COLORS["completed"] == "success"

    def test_has_color_for_failed(self):
        """Test has color for failed"""
        assert PURCHASE_STATUS["FAILED"] in PURCHASE_STATUS_COLORS
        assert PURCHASE_STATUS_COLORS["failed"] == "error"


# =============================================================================
# get_status_label function tests
# =============================================================================
class TestGetStatusLabel:
    """Tests for get_status_label function"""

    def test_pending_label(self):
        """Test getting pending label"""
        result = get_status_label("pending")
        assert result == "ממתין"

    def test_completed_label(self):
        """Test getting completed label"""
        result = get_status_label("completed")
        assert result == "הושלם"

    def test_failed_label(self):
        """Test getting failed label"""
        result = get_status_label("failed")
        assert result == "נכשל"

    def test_unknown_status_returns_original(self):
        """Test unknown status returns original value"""
        result = get_status_label("unknown_status")
        assert result == "unknown_status"


# =============================================================================
# get_status_color function tests
# =============================================================================
class TestGetStatusColor:
    """Tests for get_status_color function"""

    def test_pending_color(self):
        """Test getting pending color"""
        result = get_status_color("pending")
        assert result == "processing"

    def test_completed_color(self):
        """Test getting completed color"""
        result = get_status_color("completed")
        assert result == "success"

    def test_failed_color(self):
        """Test getting failed color"""
        result = get_status_color("failed")
        assert result == "error"

    def test_unknown_status_returns_default(self):
        """Test unknown status returns default"""
        result = get_status_color("unknown_status")
        assert result == "default"


# =============================================================================
# is_final_status function tests
# =============================================================================
class TestIsFinalStatus:
    """Tests for is_final_status function"""

    def test_pending_is_not_final(self):
        """Test pending is not final"""
        result = is_final_status("pending")
        assert result is False

    def test_completed_is_final(self):
        """Test completed is final"""
        result = is_final_status("completed")
        assert result is True

    def test_failed_is_final(self):
        """Test failed is final"""
        result = is_final_status("failed")
        assert result is True

    def test_unknown_status_is_not_final(self):
        """Test unknown status is not final"""
        result = is_final_status("unknown")
        assert result is False


# =============================================================================
# get_status_from_nedarim function tests
# =============================================================================
class TestGetStatusFromNedarim:
    """Tests for get_status_from_nedarim function"""

    def test_error_returns_failed(self):
        """Test Nedarim Error returns failed status"""
        result = get_status_from_nedarim("Error")
        assert result == "failed"

    def test_success_returns_completed(self):
        """Test Nedarim success returns completed status"""
        result = get_status_from_nedarim("Success")
        assert result == "completed"

    def test_any_non_error_returns_completed(self):
        """Test any non-Error response returns completed"""
        result = get_status_from_nedarim("OK")
        assert result == "completed"

    def test_empty_string_returns_completed(self):
        """Test empty string returns completed"""
        result = get_status_from_nedarim("")
        assert result == "completed"
