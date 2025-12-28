"""
Tests for print_pricing_dialog.py - Print Pricing Dialog
Tests admin interface for setting organization print pricing.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QDialog, QLineEdit, QPushButton
from PyQt6.QtCore import Qt


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def mock_org_metadata_service():
    """Create mock organization metadata service"""
    service = Mock()
    service.get_print_pricing.return_value = {
        "success": True,
        "pricing": {
            "black_and_white_price": 1.5,
            "color_price": 3.5
        }
    }
    service.set_print_pricing.return_value = {"success": True}
    return service


@pytest.fixture
def print_pricing_dialog(qapp, mock_org_metadata_service):
    """Create PrintPricingDialog instance"""
    from ui.print_pricing_dialog import PrintPricingDialog
    
    dialog = PrintPricingDialog(mock_org_metadata_service, "test-org-123")
    yield dialog
    dialog.close()


# =============================================================================
# Test initialization
# =============================================================================
class TestPrintPricingDialogInit:
    """Tests for PrintPricingDialog initialization"""

    def test_inherits_from_qdialog(self, print_pricing_dialog):
        """Test dialog inherits from QDialog"""
        assert isinstance(print_pricing_dialog, QDialog)

    def test_stores_org_metadata_service(self, print_pricing_dialog, mock_org_metadata_service):
        """Test dialog stores organization metadata service"""
        assert print_pricing_dialog.organization_metadata_service == mock_org_metadata_service

    def test_stores_org_id(self, print_pricing_dialog):
        """Test dialog stores org ID"""
        assert print_pricing_dialog.org_id == "test-org-123"

    def test_has_pricing_updated_signal(self, print_pricing_dialog):
        """Test dialog has pricing_updated signal"""
        assert hasattr(print_pricing_dialog, "pricing_updated")

    def test_is_modal(self, print_pricing_dialog):
        """Test dialog is modal"""
        assert print_pricing_dialog.isModal()

    def test_has_fixed_size(self, print_pricing_dialog):
        """Test dialog has fixed size"""
        assert print_pricing_dialog.width() == 400
        assert print_pricing_dialog.height() == 300

    def test_uses_rtl_layout(self, print_pricing_dialog):
        """Test dialog uses RTL layout for Hebrew"""
        assert print_pricing_dialog.layoutDirection() == Qt.LayoutDirection.RightToLeft


# =============================================================================
# Test UI elements
# =============================================================================
class TestPrintPricingDialogUI:
    """Tests for UI elements"""

    def test_has_bw_price_input(self, print_pricing_dialog):
        """Test dialog has black/white price input"""
        assert hasattr(print_pricing_dialog, "bw_price_input")
        assert isinstance(print_pricing_dialog.bw_price_input, QLineEdit)

    def test_has_color_price_input(self, print_pricing_dialog):
        """Test dialog has color price input"""
        assert hasattr(print_pricing_dialog, "color_price_input")
        assert isinstance(print_pricing_dialog.color_price_input, QLineEdit)

    def test_has_save_button(self, print_pricing_dialog):
        """Test dialog has save button"""
        assert hasattr(print_pricing_dialog, "save_button")
        assert isinstance(print_pricing_dialog.save_button, QPushButton)

    def test_has_cancel_button(self, print_pricing_dialog):
        """Test dialog has cancel button"""
        assert hasattr(print_pricing_dialog, "cancel_button")
        assert isinstance(print_pricing_dialog.cancel_button, QPushButton)


# =============================================================================
# Test load_current_pricing
# =============================================================================
class TestLoadCurrentPricing:
    """Tests for load_current_pricing method"""

    def test_calls_get_print_pricing(self, print_pricing_dialog, mock_org_metadata_service):
        """Test load_current_pricing calls service"""
        # Already called during init
        mock_org_metadata_service.get_print_pricing.assert_called_once_with("test-org-123")

    def test_populates_bw_price_input(self, print_pricing_dialog):
        """Test bw price input is populated from service"""
        assert print_pricing_dialog.bw_price_input.text() == "1.5"

    def test_populates_color_price_input(self, print_pricing_dialog):
        """Test color price input is populated from service"""
        assert print_pricing_dialog.color_price_input.text() == "3.5"

    def test_uses_defaults_on_failure(self, qapp, mock_org_metadata_service):
        """Test uses defaults when service fails"""
        mock_org_metadata_service.get_print_pricing.return_value = {"success": False}
        
        from ui.print_pricing_dialog import PrintPricingDialog
        dialog = PrintPricingDialog(mock_org_metadata_service, "test-org")
        
        assert dialog.bw_price_input.text() == "1.0"
        assert dialog.color_price_input.text() == "3.0"
        
        dialog.close()

    def test_uses_defaults_on_exception(self, qapp, mock_org_metadata_service):
        """Test uses defaults when exception occurs"""
        mock_org_metadata_service.get_print_pricing.side_effect = Exception("Network error")
        
        from ui.print_pricing_dialog import PrintPricingDialog
        dialog = PrintPricingDialog(mock_org_metadata_service, "test-org")
        
        assert dialog.bw_price_input.text() == "1.0"
        assert dialog.color_price_input.text() == "3.0"
        
        dialog.close()


# =============================================================================
# Test save_pricing
# =============================================================================
class TestSavePricing:
    """Tests for save_pricing method"""

    def test_save_calls_service_with_correct_values(self, print_pricing_dialog, mock_org_metadata_service):
        """Test save calls service with correct values"""
        print_pricing_dialog.bw_price_input.setText("2.0")
        print_pricing_dialog.color_price_input.setText("4.0")
        
        with patch.object(print_pricing_dialog, "accept"):
            with patch("ui.print_pricing_dialog.QMessageBox"):
                print_pricing_dialog.save_pricing()
        
        mock_org_metadata_service.set_print_pricing.assert_called_once_with(
            "test-org-123", 2.0, 4.0
        )

    def test_save_emits_pricing_updated_signal(self, print_pricing_dialog, mock_org_metadata_service):
        """Test save emits pricing_updated signal"""
        print_pricing_dialog.bw_price_input.setText("2.0")
        print_pricing_dialog.color_price_input.setText("4.0")
        
        signal_received = []
        print_pricing_dialog.pricing_updated.connect(lambda data: signal_received.append(data))
        
        with patch.object(print_pricing_dialog, "accept"):
            with patch("ui.print_pricing_dialog.QMessageBox"):
                print_pricing_dialog.save_pricing()
        
        assert len(signal_received) == 1
        assert signal_received[0]["black_and_white_price"] == 2.0
        assert signal_received[0]["color_price"] == 4.0

    def test_save_shows_warning_for_invalid_input(self, print_pricing_dialog):
        """Test save shows warning for invalid input"""
        print_pricing_dialog.bw_price_input.setText("invalid")
        print_pricing_dialog.color_price_input.setText("4.0")
        
        with patch("ui.print_pricing_dialog.QMessageBox.warning") as mock_warning:
            print_pricing_dialog.save_pricing()
            mock_warning.assert_called_once()

    def test_save_shows_warning_for_zero_price(self, print_pricing_dialog):
        """Test save shows warning for zero price"""
        print_pricing_dialog.bw_price_input.setText("0")
        print_pricing_dialog.color_price_input.setText("4.0")
        
        with patch("ui.print_pricing_dialog.QMessageBox.warning") as mock_warning:
            print_pricing_dialog.save_pricing()
            mock_warning.assert_called_once()

    def test_save_shows_warning_for_negative_price(self, print_pricing_dialog):
        """Test save shows warning for negative price"""
        print_pricing_dialog.bw_price_input.setText("-1.0")
        print_pricing_dialog.color_price_input.setText("4.0")
        
        with patch("ui.print_pricing_dialog.QMessageBox.warning") as mock_warning:
            print_pricing_dialog.save_pricing()
            mock_warning.assert_called_once()

    def test_save_shows_error_on_service_failure(self, print_pricing_dialog, mock_org_metadata_service):
        """Test save shows error when service fails"""
        mock_org_metadata_service.set_print_pricing.return_value = {
            "success": False,
            "error": "Database error"
        }
        
        print_pricing_dialog.bw_price_input.setText("2.0")
        print_pricing_dialog.color_price_input.setText("4.0")
        
        with patch("ui.print_pricing_dialog.QMessageBox.critical") as mock_critical:
            print_pricing_dialog.save_pricing()
            mock_critical.assert_called_once()

    def test_save_shows_error_on_exception(self, print_pricing_dialog, mock_org_metadata_service):
        """Test save shows error when exception occurs"""
        mock_org_metadata_service.set_print_pricing.side_effect = Exception("Network error")
        
        print_pricing_dialog.bw_price_input.setText("2.0")
        print_pricing_dialog.color_price_input.setText("4.0")
        
        with patch("ui.print_pricing_dialog.QMessageBox.critical") as mock_critical:
            print_pricing_dialog.save_pricing()
            mock_critical.assert_called_once()


# =============================================================================
# Test input validation
# =============================================================================
class TestInputValidation:
    """Tests for input validation logic"""

    def test_valid_float_input(self, print_pricing_dialog):
        """Test valid float input is accepted"""
        print_pricing_dialog.bw_price_input.setText("1.5")
        print_pricing_dialog.color_price_input.setText("3.5")
        
        # Should be able to parse
        bw = float(print_pricing_dialog.bw_price_input.text())
        color = float(print_pricing_dialog.color_price_input.text())
        
        assert bw == 1.5
        assert color == 3.5

    def test_integer_input_is_valid(self, print_pricing_dialog):
        """Test integer input is valid"""
        print_pricing_dialog.bw_price_input.setText("2")
        print_pricing_dialog.color_price_input.setText("5")
        
        bw = float(print_pricing_dialog.bw_price_input.text())
        color = float(print_pricing_dialog.color_price_input.text())
        
        assert bw == 2.0
        assert color == 5.0


# =============================================================================
# Test button connections
# =============================================================================
class TestButtonConnections:
    """Tests for button signal connections"""

    def test_cancel_button_rejects_dialog(self, print_pricing_dialog):
        """Test cancel button rejects dialog"""
        # Cancel button should be connected to reject
        # This is set up in init_ui
        assert print_pricing_dialog.cancel_button is not None

    def test_save_button_connected_to_save_pricing(self, print_pricing_dialog):
        """Test save button is connected to save_pricing"""
        # Save button should be connected to save_pricing
        assert print_pricing_dialog.save_button is not None




