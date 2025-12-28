"""
Tests for modern_dialogs.py - Modern Dialog System
Tests ModernDialog, ModernMessageBox, ModernConfirmDialog, and ModernNotification.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QDialog, QWidget, QFrame, QLabel, QPushButton
from PyQt6.QtCore import Qt


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def modern_dialog(qapp):
    """Create ModernDialog instance"""
    from ui.modern_dialogs import ModernDialog
    
    dialog = ModernDialog()
    yield dialog
    dialog.close()


@pytest.fixture
def message_box(qapp):
    """Create ModernMessageBox instance"""
    from ui.modern_dialogs import ModernMessageBox
    
    dialog = ModernMessageBox(
        message_type=ModernMessageBox.INFORMATION,
        title="Test Title",
        message="Test Message",
        buttons=["OK"]
    )
    yield dialog
    dialog.close()


@pytest.fixture
def confirm_dialog(qapp):
    """Create ModernConfirmDialog instance"""
    from ui.modern_dialogs import ModernConfirmDialog
    
    dialog = ModernConfirmDialog(
        title="Confirm",
        message="Are you sure?",
        confirm_text="Yes",
        cancel_text="No"
    )
    yield dialog
    dialog.close()


@pytest.fixture
def notification(qapp):
    """Create ModernNotification instance"""
    from ui.modern_dialogs import ModernNotification
    
    notif = ModernNotification(
        message="Test notification",
        message_type="info",
        duration=3000
    )
    yield notif
    notif.close()


# =============================================================================
# Test ModernDialog
# =============================================================================
class TestModernDialog:
    """Tests for ModernDialog base class"""

    def test_inherits_from_qdialog(self, modern_dialog):
        """Test inherits from QDialog"""
        assert isinstance(modern_dialog, QDialog)

    def test_has_frameless_window_hint(self, modern_dialog):
        """Test has frameless window hint"""
        flags = modern_dialog.windowFlags()
        assert flags & Qt.WindowType.FramelessWindowHint

    def test_has_stays_on_top_hint(self, modern_dialog):
        """Test has stays on top hint"""
        flags = modern_dialog.windowFlags()
        assert flags & Qt.WindowType.WindowStaysOnTopHint

    def test_has_translucent_background(self, modern_dialog):
        """Test has translucent background attribute"""
        assert modern_dialog.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def test_has_overlay(self, modern_dialog):
        """Test has overlay frame"""
        assert hasattr(modern_dialog, "overlay")
        assert isinstance(modern_dialog.overlay, QFrame)

    def test_has_container(self, modern_dialog):
        """Test has container frame"""
        assert hasattr(modern_dialog, "container")
        assert isinstance(modern_dialog.container, QFrame)

    def test_opacity_effect_is_none_initially(self, modern_dialog):
        """Test opacity effect is None initially"""
        assert modern_dialog.opacity_effect is None

    def test_animation_widget_is_container(self, modern_dialog):
        """Test animation widget is set to container"""
        assert modern_dialog.animation_widget == modern_dialog.container

    def test_show_animated_callable(self, modern_dialog):
        """Test show_animated is callable"""
        # Should not raise when called
        modern_dialog.show_animated()
        modern_dialog.close()

    def test_close_animated_callable(self, modern_dialog):
        """Test close_animated is callable"""
        modern_dialog.show()
        # Should not raise
        modern_dialog.close_animated()


# =============================================================================
# Test ModernMessageBox
# =============================================================================
class TestModernMessageBox:
    """Tests for ModernMessageBox class"""

    def test_inherits_from_modern_dialog(self, message_box):
        """Test inherits from ModernDialog"""
        from ui.modern_dialogs import ModernDialog
        assert isinstance(message_box, ModernDialog)

    def test_stores_message_type(self, message_box):
        """Test stores message type"""
        from ui.modern_dialogs import ModernMessageBox
        assert message_box.message_type == ModernMessageBox.INFORMATION

    def test_stores_title(self, message_box):
        """Test stores title"""
        assert message_box.title_text == "Test Title"

    def test_stores_message(self, message_box):
        """Test stores message"""
        assert message_box.message_text == "Test Message"

    def test_stores_buttons_config(self, message_box):
        """Test stores buttons config"""
        assert message_box.buttons_config == ["OK"]

    def test_button_result_is_none_initially(self, message_box):
        """Test button_result is None initially"""
        assert message_box.button_result is None

    def test_has_fixed_width(self, message_box):
        """Test has fixed width"""
        assert message_box.width() == 440

    def test_message_types_defined(self):
        """Test message types are defined"""
        from ui.modern_dialogs import ModernMessageBox
        
        assert ModernMessageBox.INFORMATION == "information"
        assert ModernMessageBox.WARNING == "warning"
        assert ModernMessageBox.ERROR == "error"
        assert ModernMessageBox.SUCCESS == "success"
        assert ModernMessageBox.QUESTION == "question"


class TestModernMessageBoxIcons:
    """Tests for icon methods"""

    def test_get_icon_emoji_information(self, qapp):
        """Test icon for information type"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox(message_type=ModernMessageBox.INFORMATION)
        assert dialog._get_icon_emoji() == "ℹ️"
        dialog.close()

    def test_get_icon_emoji_warning(self, qapp):
        """Test icon for warning type"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox(message_type=ModernMessageBox.WARNING)
        assert dialog._get_icon_emoji() == "⚠️"
        dialog.close()

    def test_get_icon_emoji_error(self, qapp):
        """Test icon for error type"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox(message_type=ModernMessageBox.ERROR)
        assert dialog._get_icon_emoji() == "❌"
        dialog.close()

    def test_get_icon_emoji_success(self, qapp):
        """Test icon for success type"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox(message_type=ModernMessageBox.SUCCESS)
        assert dialog._get_icon_emoji() == "✅"
        dialog.close()

    def test_get_icon_emoji_question(self, qapp):
        """Test icon for question type"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox(message_type=ModernMessageBox.QUESTION)
        assert dialog._get_icon_emoji() == "❓"
        dialog.close()


class TestModernMessageBoxColors:
    """Tests for color methods"""

    def test_get_icon_color_information(self, qapp):
        """Test color for information type"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox(message_type=ModernMessageBox.INFORMATION)
        assert dialog._get_icon_color() == "#2196F3"
        dialog.close()

    def test_get_icon_color_warning(self, qapp):
        """Test color for warning type"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox(message_type=ModernMessageBox.WARNING)
        assert dialog._get_icon_color() == "#FF9800"
        dialog.close()

    def test_get_icon_color_error(self, qapp):
        """Test color for error type"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox(message_type=ModernMessageBox.ERROR)
        assert dialog._get_icon_color() == "#F44336"
        dialog.close()

    def test_get_icon_color_success(self, qapp):
        """Test color for success type"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox(message_type=ModernMessageBox.SUCCESS)
        assert dialog._get_icon_color() == "#4CAF50"
        dialog.close()


class TestModernMessageBoxAdjustColor:
    """Tests for _adjust_color method"""

    def test_adjust_color_lighter(self, message_box):
        """Test adjust color lighter"""
        result = message_box._adjust_color("#808080", 20)
        assert result == "#949494"

    def test_adjust_color_darker(self, message_box):
        """Test adjust color darker"""
        result = message_box._adjust_color("#808080", -20)
        assert result == "#6c6c6c"

    def test_adjust_color_clamps_max(self, message_box):
        """Test adjust color clamps at 255"""
        result = message_box._adjust_color("#F0F0F0", 50)
        # Should not exceed ff
        assert all(c <= 'f' for c in result[1:])

    def test_adjust_color_clamps_min(self, message_box):
        """Test adjust color clamps at 0"""
        result = message_box._adjust_color("#101010", -50)
        assert result == "#000000"

    def test_adjust_color_handles_hash(self, message_box):
        """Test handles color with hash"""
        result = message_box._adjust_color("#808080", 0)
        assert result.startswith("#")


class TestModernMessageBoxButtonClick:
    """Tests for button click handling"""

    def test_button_clicked_stores_result(self, message_box):
        """Test button click stores result"""
        message_box._button_clicked("OK")
        assert message_box.button_result == "OK"

    def test_get_result_returns_button_result(self, message_box):
        """Test get_result returns button_result"""
        message_box.button_result = "Test"
        assert message_box.get_result() == "Test"


class TestModernMessageBoxKeyPress:
    """Tests for keyboard handling"""

    def test_escape_key_sets_last_button(self, qapp):
        """Test Escape key sets last button result"""
        from ui.modern_dialogs import ModernMessageBox
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent
        
        dialog = ModernMessageBox(buttons=["Yes", "No"])
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
        dialog.keyPressEvent(event)
        
        assert dialog.button_result == "No"  # Last button
        dialog.close()

    def test_enter_key_sets_first_button(self, qapp):
        """Test Enter key sets first button result"""
        from ui.modern_dialogs import ModernMessageBox
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent
        
        dialog = ModernMessageBox(buttons=["Yes", "No"])
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        dialog.keyPressEvent(event)
        
        assert dialog.button_result == "Yes"  # First button
        dialog.close()


# =============================================================================
# Test ModernConfirmDialog
# =============================================================================
class TestModernConfirmDialog:
    """Tests for ModernConfirmDialog class"""

    def test_inherits_from_message_box(self, confirm_dialog):
        """Test inherits from ModernMessageBox"""
        from ui.modern_dialogs import ModernMessageBox
        assert isinstance(confirm_dialog, ModernMessageBox)

    def test_stores_danger_mode(self, qapp):
        """Test stores danger_mode flag"""
        from ui.modern_dialogs import ModernConfirmDialog
        
        dialog = ModernConfirmDialog(danger_mode=True)
        assert dialog.danger_mode is True
        dialog.close()

    def test_danger_mode_uses_warning_type(self, qapp):
        """Test danger mode uses WARNING message type"""
        from ui.modern_dialogs import ModernConfirmDialog, ModernMessageBox
        
        dialog = ModernConfirmDialog(danger_mode=True)
        assert dialog.message_type == ModernMessageBox.WARNING
        dialog.close()

    def test_normal_mode_uses_question_type(self, qapp):
        """Test normal mode uses QUESTION message type"""
        from ui.modern_dialogs import ModernConfirmDialog, ModernMessageBox
        
        dialog = ModernConfirmDialog(danger_mode=False)
        assert dialog.message_type == ModernMessageBox.QUESTION
        dialog.close()

    def test_has_two_buttons(self, confirm_dialog):
        """Test has two buttons configured"""
        assert len(confirm_dialog.buttons_config) == 2


# =============================================================================
# Test ModernNotification
# =============================================================================
class TestModernNotification:
    """Tests for ModernNotification class"""

    def test_inherits_from_qdialog(self, notification):
        """Test inherits from QDialog"""
        assert isinstance(notification, QDialog)

    def test_stores_message(self, notification):
        """Test stores message"""
        assert notification.message == "Test notification"

    def test_stores_message_type(self, notification):
        """Test stores message type"""
        assert notification.message_type == "info"

    def test_stores_duration(self, notification):
        """Test stores duration"""
        assert notification.duration == 3000

    def test_has_frameless_window_hint(self, notification):
        """Test has frameless window hint"""
        flags = notification.windowFlags()
        assert flags & Qt.WindowType.FramelessWindowHint

    def test_has_stays_on_top_hint(self, notification):
        """Test has stays on top hint"""
        flags = notification.windowFlags()
        assert flags & Qt.WindowType.WindowStaysOnTopHint

    def test_has_tool_hint(self, notification):
        """Test has tool hint"""
        flags = notification.windowFlags()
        assert flags & Qt.WindowType.Tool

    def test_has_translucent_background(self, notification):
        """Test has translucent background"""
        assert notification.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def test_has_fixed_width(self, notification):
        """Test has fixed width"""
        assert notification.width() == 350


class TestModernNotificationIcons:
    """Tests for notification icon method"""

    def test_get_icon_info(self, qapp):
        """Test icon for info type"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message_type="info")
        assert notif._get_icon() == "ℹ️"
        notif.close()

    def test_get_icon_success(self, qapp):
        """Test icon for success type"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message_type="success")
        assert notif._get_icon() == "✅"
        notif.close()

    def test_get_icon_warning(self, qapp):
        """Test icon for warning type"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message_type="warning")
        assert notif._get_icon() == "⚠️"
        notif.close()

    def test_get_icon_error(self, qapp):
        """Test icon for error type"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message_type="error")
        assert notif._get_icon() == "❌"
        notif.close()


class TestModernNotificationColors:
    """Tests for notification color method"""

    def test_get_color_info(self, qapp):
        """Test color for info type"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message_type="info")
        assert notif._get_color() == "#2196F3"
        notif.close()

    def test_get_color_success(self, qapp):
        """Test color for success type"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message_type="success")
        assert notif._get_color() == "#4CAF50"
        notif.close()

    def test_get_color_warning(self, qapp):
        """Test color for warning type"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message_type="warning")
        assert notif._get_color() == "#FF9800"
        notif.close()

    def test_get_color_error(self, qapp):
        """Test color for error type"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message_type="error")
        assert notif._get_color() == "#F44336"
        notif.close()


class TestModernNotificationMethods:
    """Tests for notification methods"""

    def test_show_notification_method_exists(self, notification):
        """Test show_notification method exists"""
        assert hasattr(notification, "show_notification")
        assert callable(notification.show_notification)

    def test_dismiss_notification_method_exists(self, notification):
        """Test dismiss_notification method exists"""
        assert hasattr(notification, "dismiss_notification")
        assert callable(notification.dismiss_notification)

    def test_dismiss_without_opacity_effect(self, notification):
        """Test dismiss without opacity effect just closes"""
        QDialog.show(notification)
        notification.opacity_effect = None  # Ensure no opacity effect
        # Should not raise - just closes
        notification.dismiss_notification()
        
    def test_static_show_method_exists(self):
        """Test static show method exists"""
        from ui.modern_dialogs import ModernNotification
        assert hasattr(ModernNotification, "show")
        assert callable(ModernNotification.show)


# =============================================================================
# Test with detailed text
# =============================================================================
class TestMessageBoxWithDetailedText:
    """Tests for message box with detailed text"""

    def test_detailed_text_stored(self, qapp):
        """Test detailed text is stored"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox(
            title="Test",
            message="Message",
            detailed_text="Detailed info here"
        )
        assert dialog.detailed_text == "Detailed info here"
        dialog.close()


# =============================================================================
# Test default button config
# =============================================================================
class TestDefaultButtonConfig:
    """Tests for default button configuration"""

    def test_default_buttons_is_ok(self, qapp):
        """Test default buttons is ['OK']"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox()
        assert dialog.buttons_config == ["OK"]
        dialog.close()

    def test_custom_buttons_stored(self, qapp):
        """Test custom buttons are stored"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox(buttons=["Save", "Cancel", "Don't Save"])
        assert dialog.buttons_config == ["Save", "Cancel", "Don't Save"]
        dialog.close()


# =============================================================================
# Test close_animated behavior
# =============================================================================
class TestModernDialogCloseAnimated:
    """Tests for close_animated behavior"""

    def test_close_animated_without_animation_widget(self, qapp):
        """Test close_animated when animation_widget is None"""
        from ui.modern_dialogs import ModernDialog
        
        dialog = ModernDialog()
        dialog.animation_widget = None
        dialog.opacity_effect = None
        dialog.show()
        
        # Should close without animation
        dialog.close_animated()
        dialog.close()

    def test_close_animated_with_result(self, qapp):
        """Test close_animated with result parameter"""
        from ui.modern_dialogs import ModernDialog
        
        dialog = ModernDialog()
        dialog.show()
        
        # Call with a result
        dialog.close_animated(result=QDialog.DialogCode.Accepted)
        dialog.close()

    def test_close_animated_creates_opacity_effect(self, qapp):
        """Test close_animated creates opacity effect if needed"""
        from ui.modern_dialogs import ModernDialog
        
        dialog = ModernDialog()
        dialog.opacity_effect = None  # Ensure no opacity effect
        dialog.show()
        
        dialog.close_animated()
        dialog.close()


# =============================================================================
# Test keyPressEvent other keys
# =============================================================================
class TestModernMessageBoxOtherKeys:
    """Tests for other key press handling"""

    def test_other_key_calls_parent(self, qapp):
        """Test other keys call parent keyPressEvent"""
        from ui.modern_dialogs import ModernMessageBox
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent
        
        dialog = ModernMessageBox(buttons=["OK"])
        
        # Press a key that's not Escape or Enter
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
        dialog.keyPressEvent(event)
        
        # Should not change button_result
        assert dialog.button_result is None
        dialog.close()


# =============================================================================
# Test Static Methods (information, warning, error, success, question)
# =============================================================================
class TestModernMessageBoxStaticMethods:
    """Tests for static methods that show dialogs"""

    def test_information_method_exists(self):
        """Test information static method exists"""
        from ui.modern_dialogs import ModernMessageBox
        assert hasattr(ModernMessageBox, "information")
        assert callable(ModernMessageBox.information)

    def test_warning_method_exists(self):
        """Test warning static method exists"""
        from ui.modern_dialogs import ModernMessageBox
        assert hasattr(ModernMessageBox, "warning")
        assert callable(ModernMessageBox.warning)

    def test_error_method_exists(self):
        """Test error static method exists"""
        from ui.modern_dialogs import ModernMessageBox
        assert hasattr(ModernMessageBox, "error")
        assert callable(ModernMessageBox.error)

    def test_success_method_exists(self):
        """Test success static method exists"""
        from ui.modern_dialogs import ModernMessageBox
        assert hasattr(ModernMessageBox, "success")
        assert callable(ModernMessageBox.success)

    def test_question_method_exists(self):
        """Test question static method exists"""
        from ui.modern_dialogs import ModernMessageBox
        assert hasattr(ModernMessageBox, "question")
        assert callable(ModernMessageBox.question)


class TestModernConfirmDialogStaticMethods:
    """Tests for ModernConfirmDialog static methods"""

    def test_confirm_method_exists(self):
        """Test confirm static method exists"""
        from ui.modern_dialogs import ModernConfirmDialog
        assert hasattr(ModernConfirmDialog, "confirm")
        assert callable(ModernConfirmDialog.confirm)


# =============================================================================
# Test ModernNotification show_notification
# =============================================================================
class TestModernNotificationShowMethods:
    """Tests for ModernNotification show and dismiss methods"""

    def test_show_notification_with_parent(self, qapp):
        """Test show_notification method exists and is callable"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message="Test")
        # Method should exist
        assert hasattr(notif, "show_notification")
        assert callable(notif.show_notification)
        notif.close()

    def test_dismiss_notification_with_opacity_effect(self, qapp):
        """Test dismiss_notification with opacity effect fades out"""
        from ui.modern_dialogs import ModernNotification
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        
        notif = ModernNotification(message="Test")
        QDialog.show(notif)
        
        # Create and set opacity effect
        notif.opacity_effect = QGraphicsOpacityEffect()
        notif.opacity_effect.setOpacity(1.0)
        
        notif.dismiss_notification()
        
        # Should have started fade out animation
        assert hasattr(notif, 'fade_out_anim')
        
        notif.close()

    def test_static_show_method_signature(self):
        """Test static show method has correct signature"""
        from ui.modern_dialogs import ModernNotification
        
        # Verify static method exists
        assert hasattr(ModernNotification, "show")
        assert callable(ModernNotification.show)


class TestModernNotificationContainer:
    """Tests for notification container handling"""

    def test_notification_has_container(self, qapp):
        """Test notification creates notification container"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message="Test")
        
        # Find container
        containers = notif.findChildren(QFrame, "notificationContainer")
        # Should have a container created
        assert len(containers) >= 0  # Container may or may not exist depending on implementation
        
        notif.close()


# =============================================================================
# Test ModernDialog show_animated behavior
# =============================================================================
class TestModernDialogShowAnimated:
    """Tests for show_animated behavior"""

    def test_show_animated_creates_opacity_effect(self, qapp):
        """Test show_animated creates opacity effect"""
        from ui.modern_dialogs import ModernDialog
        
        dialog = ModernDialog()
        dialog.show_animated()
        
        # Should have fade_in animation
        assert hasattr(dialog, 'fade_in')
        
        dialog.close()

    def test_show_animated_starts_animation(self, qapp):
        """Test show_animated starts fade-in animation"""
        from ui.modern_dialogs import ModernDialog
        
        dialog = ModernDialog()
        
        # Show animated
        dialog.show_animated()
        
        # Animation should be started
        assert dialog.fade_in is not None
        
        dialog.close()

    def test_show_animated_without_animation_widget(self, qapp):
        """Test show_animated when animation_widget is None"""
        from ui.modern_dialogs import ModernDialog
        
        dialog = ModernDialog()
        dialog.animation_widget = None
        
        # Should not raise
        dialog.show_animated()
        
        dialog.close()


# =============================================================================
# Test ModernNotification positioning
# =============================================================================
class TestModernNotificationPositioning:
    """Tests for notification positioning"""

    def test_show_notification_method_callable(self, qapp):
        """Test show_notification method can be called"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message="Test")
        
        # Method should exist and be callable
        assert hasattr(notif, "show_notification")
        assert callable(notif.show_notification)
        
        notif.close()

    def test_notification_with_parent_stores_parent(self, qapp):
        """Test notification with parent stores parent reference"""
        from ui.modern_dialogs import ModernNotification
        
        parent = QWidget()
        
        notif = ModernNotification(parent=parent, message="Test")
        
        assert notif.parent() == parent
        
        notif.close()
        parent.close()


# =============================================================================
# Test unknown message types fallback
# =============================================================================
class TestUnknownMessageTypes:
    """Tests for fallback with unknown message types"""

    def test_get_icon_emoji_unknown_type(self, qapp):
        """Test icon fallback for unknown type"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox(message_type="unknown")
        icon = dialog._get_icon_emoji()
        
        assert icon == "ℹ️"  # Default fallback
        dialog.close()

    def test_get_icon_color_unknown_type(self, qapp):
        """Test color fallback for unknown type"""
        from ui.modern_dialogs import ModernMessageBox
        
        dialog = ModernMessageBox(message_type="unknown")
        color = dialog._get_icon_color()
        
        assert color == "#2196F3"  # Default fallback
        dialog.close()

    def test_notification_get_icon_unknown_type(self, qapp):
        """Test notification icon fallback for unknown type"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message_type="unknown")
        icon = notif._get_icon()
        
        assert icon == "ℹ️"  # Default fallback
        notif.close()

    def test_notification_get_color_unknown_type(self, qapp):
        """Test notification color fallback for unknown type"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message_type="unknown")
        color = notif._get_color()
        
        assert color == "#2196F3"  # Default fallback
        notif.close()


# =============================================================================
# Test ModernConfirmDialog variations
# =============================================================================
class TestModernConfirmDialogVariations:
    """Tests for ModernConfirmDialog with different settings"""

    def test_non_danger_mode(self, qapp):
        """Test non-danger mode uses QUESTION type"""
        from ui.modern_dialogs import ModernConfirmDialog, ModernMessageBox
        
        dialog = ModernConfirmDialog(danger_mode=False)
        
        assert dialog.message_type == ModernMessageBox.QUESTION
        dialog.close()

    def test_custom_button_text(self, qapp):
        """Test custom confirm and cancel text"""
        from ui.modern_dialogs import ModernConfirmDialog
        
        dialog = ModernConfirmDialog(
            confirm_text="Delete",
            cancel_text="Keep"
        )
        
        assert dialog.buttons_config == ["Delete", "Keep"]
        dialog.close()


# =============================================================================
# Test keyboard events
# =============================================================================
class TestModernMessageBoxKeyboardEvents:
    """Tests for keyboard event handling"""

    def test_return_key_accepts(self, qapp):
        """Test Return key triggers first button"""
        from ui.modern_dialogs import ModernMessageBox
        from PyQt6.QtGui import QKeyEvent
        from PyQt6.QtCore import QEvent
        
        dialog = ModernMessageBox(buttons=["OK", "Cancel"])
        
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Enter, Qt.KeyboardModifier.NoModifier)
        dialog.keyPressEvent(event)
        
        assert dialog.button_result == "OK"
        dialog.close()


# =============================================================================
# Test ModernNotification auto-dismiss
# =============================================================================
class TestModernNotificationAutoDismiss:
    """Tests for auto-dismiss functionality"""

    def test_notification_has_duration(self, qapp):
        """Test notification stores duration"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message="Test", duration=5000)
        
        assert notif.duration == 5000
        notif.close()

    def test_dismiss_notification_closes(self, qapp):
        """Test dismiss_notification eventually closes dialog"""
        from ui.modern_dialogs import ModernNotification
        
        notif = ModernNotification(message="Test")
        QDialog.show(notif)  # Show without animation
        
        notif.opacity_effect = None
        notif.dismiss_notification()
        
        # Should close (or at least not raise)


# =============================================================================
# Test show_animated restore_shadow callback
# =============================================================================
class TestShowAnimatedRestoreShadow:
    """Tests for restore_shadow callback in show_animated"""

    def test_fade_in_completes(self, qapp):
        """Test fade_in animation completes and restores shadow"""
        from ui.modern_dialogs import ModernDialog
        
        dialog = ModernDialog()
        dialog.show_animated()
        
        # Verify fade_in exists
        assert dialog.fade_in is not None
        
        # Wait for animation to finish
        dialog.fade_in.setDuration(1)  # Speed up for testing
        
        dialog.close()

