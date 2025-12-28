"""
Tests for print_dialog.py - Print Dialog
Tests print job details and budget validation before printing.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QDialog, QLabel, QPushButton
from PyQt6.QtCore import Qt


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def mock_print_validation_service():
    """Create mock print validation service"""
    service = Mock()
    service.validate_print_job.return_value = {
        "success": True,
        "can_print": True,
        "user_budget": 100.0,
        "print_cost": 5.0,
        "remaining_after_print": 95.0
    }
    # Create mock signals
    service.print_budget_insufficient = Mock()
    service.print_budget_insufficient.connect = Mock()
    service.print_budget_updated = Mock()
    service.print_budget_updated.connect = Mock()
    return service


@pytest.fixture
def print_dialog(qapp, mock_print_validation_service):
    """Create PrintDialog instance"""
    from ui.print_dialog import PrintDialog
    
    dialog = PrintDialog(mock_print_validation_service)
    yield dialog
    dialog.close()


# =============================================================================
# Test initialization
# =============================================================================
class TestPrintDialogInit:
    """Tests for PrintDialog initialization"""

    def test_inherits_from_qdialog(self, print_dialog):
        """Test dialog inherits from QDialog"""
        assert isinstance(print_dialog, QDialog)

    def test_stores_print_validation_service(self, print_dialog, mock_print_validation_service):
        """Test dialog stores print validation service"""
        assert print_dialog.print_validation_service == mock_print_validation_service

    def test_initial_page_counts_are_zero(self, print_dialog):
        """Test initial page counts are zero"""
        assert print_dialog.black_white_pages == 0
        assert print_dialog.color_pages == 0

    def test_initial_validation_result_is_none(self, print_dialog):
        """Test initial validation_result is None"""
        assert print_dialog.validation_result is None

    def test_has_print_approved_signal(self, print_dialog):
        """Test dialog has print_approved signal"""
        assert hasattr(print_dialog, "print_approved")

    def test_has_print_cancelled_signal(self, print_dialog):
        """Test dialog has print_cancelled signal"""
        assert hasattr(print_dialog, "print_cancelled")

    def test_is_modal(self, print_dialog):
        """Test dialog is modal"""
        assert print_dialog.isModal()

    def test_has_fixed_size(self, print_dialog):
        """Test dialog has fixed size"""
        assert print_dialog.width() == 400
        assert print_dialog.height() == 300

    def test_uses_rtl_layout(self, print_dialog):
        """Test dialog uses RTL layout for Hebrew"""
        assert print_dialog.layoutDirection() == Qt.LayoutDirection.RightToLeft


# =============================================================================
# Test UI elements
# =============================================================================
class TestPrintDialogUI:
    """Tests for UI elements"""

    def test_has_black_white_label(self, print_dialog):
        """Test dialog has black/white label"""
        assert hasattr(print_dialog, "black_white_label")
        assert isinstance(print_dialog.black_white_label, QLabel)

    def test_has_color_label(self, print_dialog):
        """Test dialog has color label"""
        assert hasattr(print_dialog, "color_label")
        assert isinstance(print_dialog.color_label, QLabel)

    def test_has_total_cost_label(self, print_dialog):
        """Test dialog has total cost label"""
        assert hasattr(print_dialog, "total_cost_label")
        assert isinstance(print_dialog.total_cost_label, QLabel)

    def test_has_current_budget_label(self, print_dialog):
        """Test dialog has current budget label"""
        assert hasattr(print_dialog, "current_budget_label")
        assert isinstance(print_dialog.current_budget_label, QLabel)

    def test_has_remaining_after_label(self, print_dialog):
        """Test dialog has remaining after label"""
        assert hasattr(print_dialog, "remaining_after_label")
        assert isinstance(print_dialog.remaining_after_label, QLabel)

    def test_has_status_label(self, print_dialog):
        """Test dialog has status label"""
        assert hasattr(print_dialog, "status_label")
        assert isinstance(print_dialog.status_label, QLabel)

    def test_has_print_button(self, print_dialog):
        """Test dialog has print button"""
        assert hasattr(print_dialog, "print_button")
        assert isinstance(print_dialog.print_button, QPushButton)

    def test_has_cancel_button(self, print_dialog):
        """Test dialog has cancel button"""
        assert hasattr(print_dialog, "cancel_button")
        assert isinstance(print_dialog.cancel_button, QPushButton)

    def test_print_button_initially_disabled(self, print_dialog):
        """Test print button is initially disabled"""
        assert not print_dialog.print_button.isEnabled()


# =============================================================================
# Test set_print_job
# =============================================================================
class TestSetPrintJob:
    """Tests for set_print_job method"""

    def test_stores_page_counts(self, print_dialog):
        """Test set_print_job stores page counts"""
        print_dialog.set_print_job(5, 2)
        
        assert print_dialog.black_white_pages == 5
        assert print_dialog.color_pages == 2

    def test_updates_black_white_label(self, print_dialog):
        """Test set_print_job updates black/white label"""
        print_dialog.set_print_job(5, 2)
        
        assert "5" in print_dialog.black_white_label.text()

    def test_updates_color_label(self, print_dialog):
        """Test set_print_job updates color label"""
        print_dialog.set_print_job(5, 2)
        
        assert "2" in print_dialog.color_label.text()

    def test_calls_validate_print_job(self, print_dialog, mock_print_validation_service):
        """Test set_print_job calls validate_print_job"""
        print_dialog.set_print_job(5, 2)
        
        mock_print_validation_service.validate_print_job.assert_called_once_with(5, 2)

    def test_stores_validation_result(self, print_dialog):
        """Test set_print_job stores validation result"""
        print_dialog.set_print_job(5, 2)
        
        assert print_dialog.validation_result is not None
        assert print_dialog.validation_result["success"] is True


# =============================================================================
# Test update_validation_display
# =============================================================================
class TestUpdateValidationDisplay:
    """Tests for update_validation_display method"""

    def test_enables_print_button_when_can_print(self, print_dialog):
        """Test print button is enabled when can_print is True"""
        print_dialog.set_print_job(5, 2)
        
        assert print_dialog.print_button.isEnabled()

    def test_disables_print_button_when_cannot_print(self, print_dialog, mock_print_validation_service):
        """Test print button is disabled when can_print is False"""
        mock_print_validation_service.validate_print_job.return_value = {
            "success": True,
            "can_print": False,
            "user_budget": 5.0,
            "print_cost": 10.0,
            "remaining_after_print": -5.0
        }
        
        print_dialog.set_print_job(10, 5)
        
        assert not print_dialog.print_button.isEnabled()

    def test_updates_budget_labels(self, print_dialog):
        """Test updates budget labels with correct values"""
        print_dialog.set_print_job(5, 2)
        
        assert "100.00" in print_dialog.current_budget_label.text()
        assert "5.00" in print_dialog.total_cost_label.text()
        assert "95.00" in print_dialog.remaining_after_label.text()

    def test_shows_approved_status_when_can_print(self, print_dialog):
        """Test shows approved status when can_print"""
        print_dialog.set_print_job(5, 2)
        
        assert "✅" in print_dialog.status_label.text()

    def test_shows_error_status_when_cannot_print(self, print_dialog, mock_print_validation_service):
        """Test shows error status when cannot print"""
        mock_print_validation_service.validate_print_job.return_value = {
            "success": True,
            "can_print": False,
            "user_budget": 5.0,
            "print_cost": 10.0,
            "remaining_after_print": -5.0
        }
        
        print_dialog.set_print_job(10, 5)
        
        assert "❌" in print_dialog.status_label.text()


# =============================================================================
# Test handle_insufficient_budget
# =============================================================================
class TestHandleInsufficientBudget:
    """Tests for handle_insufficient_budget method"""

    def test_updates_status_label(self, print_dialog):
        """Test updates status label with insufficient budget message"""
        print_dialog.handle_insufficient_budget(5.0, 10.0)
        
        assert "❌" in print_dialog.status_label.text()
        assert "10.00" in print_dialog.status_label.text()

    def test_disables_print_button(self, print_dialog):
        """Test disables print button"""
        print_dialog.print_button.setEnabled(True)
        
        print_dialog.handle_insufficient_budget(5.0, 10.0)
        
        assert not print_dialog.print_button.isEnabled()


# =============================================================================
# Test update_budget_display
# =============================================================================
class TestUpdateBudgetDisplay:
    """Tests for update_budget_display method"""

    def test_updates_current_budget_label(self, print_dialog):
        """Test updates current budget label"""
        print_dialog.update_budget_display(75.50)
        
        assert "75.50" in print_dialog.current_budget_label.text()


# =============================================================================
# Test approve_print
# =============================================================================
class TestApprovePrint:
    """Tests for approve_print method"""

    def test_emits_print_approved_signal(self, print_dialog):
        """Test emits print_approved signal with page counts"""
        print_dialog.set_print_job(5, 2)
        
        signal_received = []
        print_dialog.print_approved.connect(
            lambda bw, c: signal_received.append((bw, c))
        )
        
        with patch.object(print_dialog, "accept"):
            print_dialog.approve_print()
        
        assert len(signal_received) == 1
        assert signal_received[0] == (5, 2)

    def test_does_nothing_when_cannot_print(self, print_dialog, mock_print_validation_service):
        """Test does nothing when cannot print"""
        mock_print_validation_service.validate_print_job.return_value = {
            "success": True,
            "can_print": False,
            "user_budget": 5.0,
            "print_cost": 10.0,
            "remaining_after_print": -5.0
        }
        
        print_dialog.set_print_job(10, 5)
        
        signal_received = []
        print_dialog.print_approved.connect(
            lambda bw, c: signal_received.append((bw, c))
        )
        
        print_dialog.approve_print()
        
        # Signal should not be emitted
        assert len(signal_received) == 0

    def test_does_nothing_when_no_validation_result(self, print_dialog):
        """Test does nothing when no validation result"""
        print_dialog.validation_result = None
        
        signal_received = []
        print_dialog.print_approved.connect(
            lambda bw, c: signal_received.append((bw, c))
        )
        
        print_dialog.approve_print()
        
        # Signal should not be emitted
        assert len(signal_received) == 0


# =============================================================================
# Test cancel_print
# =============================================================================
class TestCancelPrint:
    """Tests for cancel_print method"""

    def test_emits_print_cancelled_signal(self, print_dialog):
        """Test emits print_cancelled signal"""
        signal_received = []
        print_dialog.print_cancelled.connect(lambda: signal_received.append(True))
        
        with patch.object(print_dialog, "reject"):
            print_dialog.cancel_print()
        
        assert len(signal_received) == 1


# =============================================================================
# Test show_error_message
# =============================================================================
class TestShowErrorMessage:
    """Tests for show_error_message method"""

    def test_updates_status_label(self, print_dialog):
        """Test updates status label with error message"""
        print_dialog.show_error_message("Test error")
        
        assert "❌" in print_dialog.status_label.text()
        assert "Test error" in print_dialog.status_label.text()

    def test_disables_print_button(self, print_dialog):
        """Test disables print button"""
        print_dialog.print_button.setEnabled(True)
        
        print_dialog.show_error_message("Test error")
        
        assert not print_dialog.print_button.isEnabled()


# =============================================================================
# Test validation error handling
# =============================================================================
class TestValidationErrorHandling:
    """Tests for validation error handling"""

    def test_shows_error_when_validation_fails(self, print_dialog, mock_print_validation_service):
        """Test shows error when validation fails"""
        mock_print_validation_service.validate_print_job.return_value = {
            "success": False,
            "error": "Service unavailable"
        }
        
        print_dialog.set_print_job(5, 2)
        
        assert "❌" in print_dialog.status_label.text()
        assert not print_dialog.print_button.isEnabled()


# =============================================================================
# Test signal types
# =============================================================================
class TestSignalTypes:
    """Tests for signal types"""

    def test_print_approved_emits_two_ints(self, print_dialog):
        """Test print_approved signal emits two integers"""
        received = []
        print_dialog.print_approved.connect(
            lambda bw, c: received.append((bw, c))
        )
        print_dialog.print_approved.emit(5, 2)
        
        assert received[0] == (5, 2)

    def test_print_cancelled_emits_nothing(self, print_dialog):
        """Test print_cancelled signal emits nothing"""
        received = []
        print_dialog.print_cancelled.connect(lambda: received.append(True))
        print_dialog.print_cancelled.emit()
        
        assert len(received) == 1





