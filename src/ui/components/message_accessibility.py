"""
Accessibility enhancements for message components.
Provides keyboard navigation, focus indicators, and screen reader support.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect


class AccessibilityEnhancer:
    """Mixin class to add accessibility features to message components."""

    def setup_accessibility(self):
        """Setup accessibility features for the component."""
        self.setup_keyboard_navigation()
        self.setup_focus_indicators()
        self.setup_screen_reader_support()

    def setup_keyboard_navigation(self):
        """Setup keyboard navigation support."""
        # Enable tab navigation
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)

        # Set accessible name and description
        if hasattr(self, "setAccessibleName"):
            self.setAccessibleName(self.get_accessible_name())
        if hasattr(self, "setAccessibleDescription"):
            self.setAccessibleDescription(self.get_accessible_description())

    def setup_focus_indicators(self):
        """Setup visual focus indicators."""
        # Create focus indicator shadow
        self.focus_shadow = QGraphicsDropShadowEffect()
        self.focus_shadow.setBlurRadius(15)
        self.focus_shadow.setXOffset(0)
        self.focus_shadow.setYOffset(0)
        self.focus_shadow.setColor(QColor(59, 130, 246, 150))  # Blue focus ring

        # Connect focus events
        self.focusInEvent = self.on_focus_in
        self.focusOutEvent = self.on_focus_out

    def setup_screen_reader_support(self):
        """Setup screen reader support."""
        # Set accessible text
        if hasattr(self, "setAccessibleText"):
            self.setAccessibleText(self.get_screen_reader_text())

    def on_focus_in(self, event):
        """Handle focus in event."""
        super().focusInEvent(event)
        if hasattr(self, "setGraphicsEffect"):
            self.setGraphicsEffect(self.focus_shadow)

        # Announce to screen reader
        self.announce_to_screen_reader()

    def on_focus_out(self, event):
        """Handle focus out event."""
        super().focusOutEvent(event)
        if hasattr(self, "setGraphicsEffect"):
            # Restore original shadow or remove effect
            if hasattr(self, "original_shadow"):
                self.setGraphicsEffect(self.original_shadow)
            else:
                self.setGraphicsEffect(None)

    def announce_to_screen_reader(self):
        """Announce current state to screen reader."""
        # This would typically use platform-specific screen reader APIs
        # For now, we'll use accessible text updates
        if hasattr(self, "setAccessibleText"):
            self.setAccessibleText(self.get_screen_reader_text())

    def get_accessible_name(self):
        """Get accessible name for screen readers."""
        return "Message component"

    def get_accessible_description(self):
        """Get accessible description for screen readers."""
        return "Interactive message component with keyboard navigation support"

    def get_screen_reader_text(self):
        """Get text for screen readers."""
        return "Message component focused"


class MessageCardAccessibility(AccessibilityEnhancer):
    """Accessibility enhancements specifically for MessageCard."""

    def get_accessible_name(self):
        """Get accessible name for message card."""
        if hasattr(self, "message_data"):
            status = "read" if self.message_data.get("isRead", False) else "unread"
            return f"Message card - {status}"
        return "Message card"

    def get_accessible_description(self):
        """Get accessible description for message card."""
        if hasattr(self, "message_data"):
            message_text = self.message_data.get("message", "No message")
            timestamp = self.message_data.get("timestamp", "Unknown time")
            return f"Message: {message_text[:100]}... Sent at {timestamp}. Click to read full message."
        return "Message card - click to read"

    def get_screen_reader_text(self):
        """Get text for screen readers."""
        if hasattr(self, "message_data"):
            status = "read" if self.message_data.get("isRead", False) else "unread"
            message_preview = self.message_data.get("message", "No message")[:50]
            return (
                f"Message card focused. Status: {status}. Preview: {message_preview}..."
            )
        return "Message card focused"

    def setup_keyboard_navigation(self):
        """Setup keyboard navigation for message card."""
        super().setup_keyboard_navigation()

        # Enable click on Enter/Space
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        """Handle keyboard events for message card."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            # Trigger click event
            if hasattr(self, "card_clicked"):
                self.card_clicked.emit(self.message_data)
        else:
            super().keyPressEvent(event)


class MessageModalAccessibility(AccessibilityEnhancer):
    """Accessibility enhancements specifically for MessageModal."""

    def get_accessible_name(self):
        """Get accessible name for message modal."""
        return "Message reading dialog"

    def get_accessible_description(self):
        """Get accessible description for message modal."""
        if hasattr(self, "messages") and self.messages:
            total = len(self.messages)
            current = getattr(self, "current_index", 0) + 1
            return f"Reading message {current} of {total}. Use Tab to navigate between buttons."
        return "Message reading dialog with navigation controls"

    def get_screen_reader_text(self):
        """Get text for screen readers."""
        if hasattr(self, "messages") and self.messages:
            total = len(self.messages)
            current = getattr(self, "current_index", 0) + 1
            return f"Message dialog opened. Reading message {current} of {total}."
        return "Message dialog opened"

    def setup_keyboard_navigation(self):
        """Setup keyboard navigation for message modal."""
        super().setup_keyboard_navigation()

        # Set tab order for buttons
        if hasattr(self, "read_all_button"):
            self.read_all_button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        if hasattr(self, "read_next_button"):
            self.read_next_button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        if hasattr(self, "close_button"):
            self.close_button.setFocusPolicy(Qt.FocusPolicy.TabFocus)

    def keyPressEvent(self, event):
        """Handle keyboard events for message modal."""
        if event.key() == Qt.Key.Key_Escape:
            if hasattr(self, "close_modal"):
                self.close_modal()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Focus on the focused button or default to read next
            focused_widget = self.focusWidget()
            if focused_widget and hasattr(focused_widget, "click"):
                focused_widget.click()
            elif hasattr(self, "read_next_message"):
                self.read_next_message()
        else:
            super().keyPressEvent(event)


class MessageNotificationAccessibility(AccessibilityEnhancer):
    """Accessibility enhancements specifically for MessageNotification."""

    def get_accessible_name(self):
        """Get accessible name for message notification."""
        return "New message notification"

    def get_accessible_description(self):
        """Get accessible description for message notification."""
        if hasattr(self, "message_count"):
            count_text = (
                f"{self.message_count} new messages"
                if self.message_count > 1
                else "1 new message"
            )
            return f"{count_text} from administrator. Click to view or press Escape to dismiss."
        return "New message notification. Click to view or press Escape to dismiss."

    def get_screen_reader_text(self):
        """Get text for screen readers."""
        if hasattr(self, "message_count"):
            count_text = (
                f"{self.message_count} new messages"
                if self.message_count > 1
                else "1 new message"
            )
            return f"Notification: {count_text} received."
        return "New message notification received."

    def setup_keyboard_navigation(self):
        """Setup keyboard navigation for message notification."""
        super().setup_keyboard_navigation()

        # Enable click on Enter/Space
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event):
        """Handle keyboard events for message notification."""
        if event.key() == Qt.Key.Key_Escape:
            if hasattr(self, "close_notification"):
                self.close_notification()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            if hasattr(self, "on_notification_clicked"):
                self.on_notification_clicked()
        else:
            super().keyPressEvent(event)


def add_accessibility_to_widget(widget, accessibility_class=None):
    """Add accessibility features to a widget."""
    if accessibility_class is None:
        accessibility_class = AccessibilityEnhancer

    # Create accessibility instance
    accessibility = accessibility_class()

    # Copy methods to widget
    for attr_name in dir(accessibility):
        if not attr_name.startswith("_") and callable(
            getattr(accessibility, attr_name)
        ):
            setattr(widget, attr_name, getattr(accessibility, attr_name))

    # Setup accessibility
    widget.setup_accessibility()

    return widget
