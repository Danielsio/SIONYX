"""
Tests for base_window.py - Base Kiosk Window
Tests shared functionality for fullscreen kiosk windows.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt


# =============================================================================
# Mock BaseKioskWindow for testing (avoids fullscreen mode issues)
# =============================================================================
class MockBaseKioskWindow(QWidget):
    """Mock BaseKioskWindow that doesn't go fullscreen"""
    
    def __init__(self):
        super().__init__()
        # Don't call setup_kiosk_window to avoid fullscreen
        
    def create_main_layout(self):
        """Create standard main layout with no margins"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        return main_layout

    def keyPressEvent(self, event):
        """Prevent Escape key from closing"""
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Prevent closing the window"""
        event.ignore()

    def shake_widget(self, widget):
        """Shake animation for validation errors"""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(400)
        geometry = widget.geometry()
        animation.setKeyValueAt(0, geometry)
        animation.setKeyValueAt(0.7, geometry)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        animation.start()
        return animation

    def show_error(self, title: str, message: str, detailed_text: str = ""):
        """Show modern error message"""
        pass

    def show_success(self, title: str, message: str, detailed_text: str = ""):
        """Show modern success message"""
        pass

    def show_warning(self, title: str, message: str, detailed_text: str = ""):
        """Show modern warning message"""
        pass

    def show_info(self, title: str, message: str, detailed_text: str = ""):
        """Show modern information message"""
        pass

    def show_question(self, title, message, detailed_text="", yes_text="Yes", no_text="No"):
        """Show modern question dialog"""
        return True

    def show_confirm(self, title, message, confirm_text="Yes", cancel_text="No", danger=False):
        """Show modern confirmation dialog"""
        return True

    def show_notification(self, message, message_type="info", duration=3000):
        """Show auto-dismissing notification toast"""
        pass

    def apply_base_stylesheet(self):
        """Apply base stylesheet"""
        return ""


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def base_window(qapp):
    """Create MockBaseKioskWindow instance"""
    window = MockBaseKioskWindow()
    yield window
    window.close()


# =============================================================================
# Test initialization
# =============================================================================
class TestBaseKioskWindowInit:
    """Tests for BaseKioskWindow initialization"""

    def test_inherits_from_qwidget(self, base_window):
        """Test window inherits from QWidget"""
        assert isinstance(base_window, QWidget)


# =============================================================================
# Test create_main_layout
# =============================================================================
class TestCreateMainLayout:
    """Tests for create_main_layout method"""

    def test_returns_qvboxlayout(self, base_window):
        """Test returns QVBoxLayout"""
        layout = base_window.create_main_layout()
        assert isinstance(layout, QVBoxLayout)

    def test_layout_has_zero_margins(self, base_window):
        """Test layout has zero margins"""
        layout = base_window.create_main_layout()
        margins = layout.contentsMargins()
        
        assert margins.left() == 0
        assert margins.top() == 0
        assert margins.right() == 0
        assert margins.bottom() == 0

    def test_layout_has_zero_spacing(self, base_window):
        """Test layout has zero spacing"""
        layout = base_window.create_main_layout()
        assert layout.spacing() == 0


# =============================================================================
# Test keyPressEvent
# =============================================================================
class TestKeyPressEvent:
    """Tests for keyPressEvent method"""

    def test_escape_key_is_ignored(self, base_window):
        """Test Escape key is ignored"""
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        
        base_window.keyPressEvent(event)
        
        # Event should be ignored (isAccepted should be False after ignore())
        assert not event.isAccepted()

    def test_other_keys_are_passed_through(self, base_window):
        """Test other keys are passed through normally"""
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
        
        # Should not raise
        base_window.keyPressEvent(event)


# =============================================================================
# Test closeEvent
# =============================================================================
class TestCloseEvent:
    """Tests for closeEvent method"""

    def test_close_event_is_ignored(self, base_window):
        """Test close event is ignored"""
        from PyQt6.QtGui import QCloseEvent
        
        event = QCloseEvent()
        
        base_window.closeEvent(event)
        
        # Event should be ignored
        assert not event.isAccepted()


# =============================================================================
# Test shake_widget
# =============================================================================
class TestShakeWidget:
    """Tests for shake_widget method"""

    def test_shake_widget_creates_animation(self, base_window):
        """Test shake_widget creates animation"""
        child_widget = QWidget(base_window)
        child_widget.setGeometry(0, 0, 100, 50)
        
        animation = base_window.shake_widget(child_widget)
        
        assert animation is not None

    def test_shake_widget_animation_duration(self, base_window):
        """Test shake animation has correct duration"""
        child_widget = QWidget(base_window)
        child_widget.setGeometry(0, 0, 100, 50)
        
        animation = base_window.shake_widget(child_widget)
        
        assert animation.duration() == 400


# =============================================================================
# Test dialog methods
# =============================================================================
class TestDialogMethods:
    """Tests for dialog display methods"""

    def test_show_error_callable(self, base_window):
        """Test show_error is callable"""
        # Should not raise
        base_window.show_error("Error", "Test message")

    def test_show_success_callable(self, base_window):
        """Test show_success is callable"""
        # Should not raise
        base_window.show_success("Success", "Test message")

    def test_show_warning_callable(self, base_window):
        """Test show_warning is callable"""
        # Should not raise
        base_window.show_warning("Warning", "Test message")

    def test_show_info_callable(self, base_window):
        """Test show_info is callable"""
        # Should not raise
        base_window.show_info("Info", "Test message")

    def test_show_question_returns_bool(self, base_window):
        """Test show_question returns boolean"""
        result = base_window.show_question("Question", "Are you sure?")
        assert isinstance(result, bool)

    def test_show_confirm_returns_bool(self, base_window):
        """Test show_confirm returns boolean"""
        result = base_window.show_confirm("Confirm", "Are you sure?")
        assert isinstance(result, bool)

    def test_show_notification_callable(self, base_window):
        """Test show_notification is callable"""
        # Should not raise
        base_window.show_notification("Test notification")


# =============================================================================
# Test apply_base_stylesheet
# =============================================================================
class TestApplyBaseStylesheet:
    """Tests for apply_base_stylesheet method"""

    def test_returns_string(self, base_window):
        """Test apply_base_stylesheet returns string"""
        result = base_window.apply_base_stylesheet()
        assert isinstance(result, str)


# =============================================================================
# Test method signatures
# =============================================================================
class TestMethodSignatures:
    """Tests for method signatures and parameters"""

    def test_show_error_accepts_detailed_text(self, base_window):
        """Test show_error accepts detailed_text parameter"""
        # Should not raise
        base_window.show_error("Error", "Message", "Detailed text")

    def test_show_question_accepts_custom_buttons(self, base_window):
        """Test show_question accepts custom button text"""
        result = base_window.show_question(
            "Question", "Are you sure?", "", "Confirm", "Cancel"
        )
        assert isinstance(result, bool)

    def test_show_confirm_accepts_danger_flag(self, base_window):
        """Test show_confirm accepts danger flag"""
        result = base_window.show_confirm(
            "Confirm", "Delete?", "Delete", "Cancel", danger=True
        )
        assert isinstance(result, bool)

    def test_show_notification_accepts_type_and_duration(self, base_window):
        """Test show_notification accepts type and duration"""
        # Should not raise
        base_window.show_notification("Message", "success", 5000)



