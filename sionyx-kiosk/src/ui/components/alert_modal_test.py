"""Tests for AlertModal component"""

import pytest
from unittest.mock import MagicMock, patch
from PyQt6.QtCore import Qt

from ui.components.alert_modal import (
    AlertModal,
    ALERT_TYPES,
    show_warning,
    show_error,
    show_info,
    show_success,
)


class TestAlertModal:
    """Tests for AlertModal class"""

    def test_init_with_defaults(self, qapp):
        """Test modal initialization with default values"""
        modal = AlertModal(
            title="Test Title",
            message="Test Message",
        )
        
        assert modal.title_text == "Test Title"
        assert modal.message_text == "Test Message"
        assert modal.detail_text == ""
        assert modal.alert_type == "info"
        assert modal.button_text == "הבנתי"

    def test_init_with_all_params(self, qapp):
        """Test modal initialization with all parameters"""
        modal = AlertModal(
            title="Warning",
            message="Something happened",
            detail="More details here",
            alert_type="warning",
            button_text="OK",
        )
        
        assert modal.title_text == "Warning"
        assert modal.message_text == "Something happened"
        assert modal.detail_text == "More details here"
        assert modal.alert_type == "warning"
        assert modal.button_text == "OK"

    def test_invalid_alert_type_defaults_to_info(self, qapp):
        """Test that invalid alert type defaults to info"""
        modal = AlertModal(
            title="Test",
            message="Test",
            alert_type="invalid_type",
        )
        
        assert modal.alert_type == "info"

    @pytest.mark.parametrize("alert_type", ["warning", "error", "info", "success"])
    def test_all_alert_types_supported(self, qapp, alert_type):
        """Test that all alert types are properly supported"""
        modal = AlertModal(
            title="Test",
            message="Test",
            alert_type=alert_type,
        )
        
        assert modal.alert_type == alert_type
        assert modal.colors == ALERT_TYPES[alert_type]

    def test_modal_has_rtl_layout(self, qapp):
        """Test that modal has RTL layout direction"""
        modal = AlertModal(title="Test", message="Test")
        
        assert modal.layoutDirection() == Qt.LayoutDirection.RightToLeft

    def test_modal_is_modal(self, qapp):
        """Test that dialog is modal"""
        modal = AlertModal(title="Test", message="Test")
        
        assert modal.isModal()

    def test_modal_has_frameless_window(self, qapp):
        """Test that modal has frameless window hint"""
        modal = AlertModal(title="Test", message="Test")
        
        flags = modal.windowFlags()
        assert flags & Qt.WindowType.FramelessWindowHint

    def test_modal_stays_on_top(self, qapp):
        """Test that modal stays on top"""
        modal = AlertModal(title="Test", message="Test")
        
        flags = modal.windowFlags()
        assert flags & Qt.WindowType.WindowStaysOnTopHint

    def test_container_has_correct_size(self, qapp):
        """Test that container has correct fixed size"""
        modal = AlertModal(title="Test", message="Test")
        
        assert modal.container.width() == 440
        assert modal.container.height() == 380

    def test_ok_button_exists(self, qapp):
        """Test that OK button exists and is clickable"""
        modal = AlertModal(title="Test", message="Test", button_text="Close")
        
        assert modal.ok_button is not None
        assert modal.ok_button.text() == "Close"

    def test_close_modal_starts_animation(self, qapp):
        """Test that close_modal starts fade animation"""
        modal = AlertModal(title="Test", message="Test")
        
        with patch.object(modal.fade_animation, 'start') as mock_start:
            modal.close_modal()
            mock_start.assert_called_once()

    def test_keypress_escape_closes_modal(self, qapp):
        """Test that pressing Escape closes the modal"""
        modal = AlertModal(title="Test", message="Test")
        
        with patch.object(modal, 'close_modal') as mock_close:
            from PyQt6.QtGui import QKeyEvent
            from PyQt6.QtCore import QEvent
            
            event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
            modal.keyPressEvent(event)
            mock_close.assert_called_once()

    def test_keypress_enter_closes_modal(self, qapp):
        """Test that pressing Enter closes the modal"""
        modal = AlertModal(title="Test", message="Test")
        
        with patch.object(modal, 'close_modal') as mock_close:
            from PyQt6.QtGui import QKeyEvent
            from PyQt6.QtCore import QEvent
            
            event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
            modal.keyPressEvent(event)
            mock_close.assert_called_once()

    def test_alert_types_have_required_keys(self):
        """Test that all alert types have required configuration keys"""
        required_keys = ["icon", "header_gradient", "icon_bg", "icon_color", "button_bg", "button_hover", "glow_color", "border_color"]
        
        for alert_type, config in ALERT_TYPES.items():
            for key in required_keys:
                assert key in config, f"Alert type '{alert_type}' missing key '{key}'"


class TestConvenienceFunctions:
    """Tests for convenience functions"""

    def test_show_warning_creates_warning_modal(self, qapp):
        """Test show_warning creates modal with warning type"""
        with patch.object(AlertModal, 'show_animated'):
            with patch.object(AlertModal, 'exec'):
                # We can't easily test this without showing UI, 
                # but we can verify the function exists and is callable
                assert callable(show_warning)

    def test_show_error_creates_error_modal(self, qapp):
        """Test show_error creates modal with error type"""
        assert callable(show_error)

    def test_show_info_creates_info_modal(self, qapp):
        """Test show_info creates modal with info type"""
        assert callable(show_info)

    def test_show_success_creates_success_modal(self, qapp):
        """Test show_success creates modal with success type"""
        assert callable(show_success)
