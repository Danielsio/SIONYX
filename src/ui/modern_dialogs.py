"""
Modern, Beautiful Dialog System
Professional UI/UX for all app dialogs
"""

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class ModernDialog(QDialog):
    """Base class for modern, beautiful dialogs"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Animation setup - apply to container, NOT the dialog itself
        self.opacity_effect = None
        self.animation_widget = None

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        """Setup the basic UI structure"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Dark overlay background
        self.overlay = QFrame()
        self.overlay.setObjectName("dialogOverlay")
        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)

        # Container with shadow effect
        self.container = QFrame()
        self.container.setObjectName("dialogContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(16)
        container_layout.setContentsMargins(24, 24, 24, 24)

        # Add dramatic drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(12)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.container.setGraphicsEffect(shadow)

        # Store reference for animation target
        self.animation_widget = self.container

        overlay_layout.addWidget(self.container)
        main_layout.addWidget(self.overlay)

    def apply_styles(self):
        """Apply modern styling with MAXIMUM contrast"""
        self.setStyleSheet(
            """
            QDialog {
                /* Subtle scrim to lift the dialog above content */
                background: rgba(0, 0, 0, 120);
            }
            
            #dialogOverlay {
                background: transparent;
                padding: 8px;
            }
            
            #dialogContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #F9FAFB);
                border-radius: 18px;
                border: 1px solid rgba(229, 231, 235, 0.8);
            }
        """
        )

    def show_animated(self):
        """Show dialog with fade-in animation"""
        # Create opacity effect for animation ONLY on the container
        if self.animation_widget and not self.opacity_effect:
            # Apply opacity effect for animation
            self.opacity_effect = QGraphicsOpacityEffect()
            self.animation_widget.setGraphicsEffect(self.opacity_effect)
            self.opacity_effect.setOpacity(0)

        self.show()

        if self.opacity_effect:
            # Fade in animation
            self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.fade_in.setDuration(250)
            self.fade_in.setStartValue(0)
            self.fade_in.setEndValue(1)
            self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

            # Restore shadow effect after animation
            def restore_shadow():
                if self.animation_widget:
                    # Create a NEW shadow effect instead of reusing the old one
                    # (Qt deletes the old effect when we replace it)
                    shadow = QGraphicsDropShadowEffect()
                    shadow.setBlurRadius(40)
                    shadow.setXOffset(0)
                    shadow.setYOffset(12)
                    shadow.setColor(QColor(0, 0, 0, 100))
                    self.animation_widget.setGraphicsEffect(shadow)
                    self.opacity_effect = None

            self.fade_in.finished.connect(restore_shadow)
            self.fade_in.start()

    def close_animated(self, result=None):
        """Close dialog with fade-out animation"""
        # Apply opacity effect for closing animation if not already present
        if self.animation_widget and not self.opacity_effect:
            self.opacity_effect = QGraphicsOpacityEffect()
            self.animation_widget.setGraphicsEffect(self.opacity_effect)
            self.opacity_effect.setOpacity(1)

        if self.opacity_effect:
            self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.fade_out.setDuration(150)
            self.fade_out.setStartValue(1)
            self.fade_out.setEndValue(0)
            self.fade_out.setEasingCurve(QEasingCurve.Type.InCubic)

            if result is not None:
                self.fade_out.finished.connect(lambda: self.done(result))
            else:
                self.fade_out.finished.connect(self.close)

            self.fade_out.start()
        else:
            # No animation, just close
            if result is not None:
                self.done(result)
            else:
                self.close()


class ModernMessageBox(ModernDialog):
    """
    Modern message box with beautiful styling
    Replaces QMessageBox with better UX
    """

    # Message types
    INFORMATION = "information"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    QUESTION = "question"

    def __init__(
        self,
        parent=None,
        message_type=INFORMATION,
        title="",
        message="",
        detailed_text="",
        buttons=None,
    ):
        self.message_type = message_type
        self.title_text = title
        self.message_text = message
        self.detailed_text = detailed_text
        self.buttons_config = buttons or ["OK"]
        self.button_result = None

        super().__init__(parent)

    def setup_ui(self):
        """Setup message box UI"""
        super().setup_ui()

        container_layout = self.container.layout()

        # Icon and title row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        # Icon
        icon_label = QLabel()
        icon_label.setObjectName("dialogIcon")
        icon_label.setFixedSize(48, 48)
        icon_label.setText(self._get_icon_emoji())
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title_label = QLabel(self.title_text)
        title_label.setObjectName("dialogTitle")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.DemiBold))
        title_label.setWordWrap(True)

        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label, 1)
        header_layout.addStretch()

        container_layout.addLayout(header_layout)

        # Message
        message_label = QLabel(self.message_text)
        message_label.setObjectName("dialogMessage")
        message_label.setFont(QFont("Segoe UI", 13))
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.RichText)
        container_layout.addWidget(message_label)

        # Detailed text (if provided)
        if self.detailed_text:
            detailed_label = QLabel(self.detailed_text)
            detailed_label.setObjectName("dialogDetailed")
            detailed_label.setFont(QFont("Segoe UI", 11))
            detailed_label.setWordWrap(True)
            detailed_label.setTextFormat(Qt.TextFormat.RichText)
            container_layout.addWidget(detailed_label)

        container_layout.addSpacing(10)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        for i, button_text in enumerate(self.buttons_config):
            btn = QPushButton(button_text)
            btn.setObjectName("dialogButton")
            btn.setMinimumWidth(100)
            btn.setMinimumHeight(44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            # Set primary style for first button
            if i == 0:
                btn.setProperty("primary", True)
                btn.setDefault(True)
                btn.setFocus()

            btn.clicked.connect(
                lambda checked, text=button_text: self._button_clicked(text)
            )
            buttons_layout.addWidget(btn)

        container_layout.addLayout(buttons_layout)

        # Set fixed width for better appearance
        self.setFixedWidth(440)

    def _get_icon_emoji(self):
        """Get emoji icon based on message type"""
        icons = {
            self.INFORMATION: "ℹ️",
            self.WARNING: "⚠️",
            self.ERROR: "❌",
            self.SUCCESS: "✅",
            self.QUESTION: "❓",
        }
        return icons.get(self.message_type, "ℹ️")

    def _get_icon_color(self):
        """Get color based on message type"""
        colors = {
            self.INFORMATION: "#2196F3",
            self.WARNING: "#FF9800",
            self.ERROR: "#F44336",
            self.SUCCESS: "#4CAF50",
            self.QUESTION: "#9C27B0",
        }
        return colors.get(self.message_type, "#2196F3")

    def _button_clicked(self, button_text):
        """Handle button click"""
        self.button_result = button_text
        self.close_animated(QDialog.DialogCode.Accepted)

    def apply_styles(self):
        """Apply modern styling to message box with better contrast"""
        super().apply_styles()

        icon_color = self._get_icon_color()

        self.setStyleSheet(
            self.styleSheet()
            + f"""
            #dialogIcon {{
                font-size: 36px;
                background: {icon_color}1F; /* ~12% */
                border: none;
                border-radius: 12px;
                padding: 4px;
            }}
            
            #dialogTitle {{
                color: #111827;
                padding-top: 2px;
                font-weight: 700;
                font-size: 18px;
            }}
            
            #dialogMessage {{
                color: #374151;
                font-size: 14px;
                font-weight: 500;
            }}
            
            #dialogDetailed {{
                color: #4B5563;
                padding: 12px;
                background: #F3F4F6;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                margin-top: 6px;
            }}
            
            #dialogButton {{
                background: #FFFFFF;
                color: #374151;
                border: 2px solid #D1D5DB;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
            }}
            
            #dialogButton:hover {{
                background: #F3F4F6;
                border-color: #9CA3AF;
                color: #111827;
            }}
            
            #dialogButton:pressed {{
                background: #E5E7EB;
                border-color: #6B7280;
                color: #111827;
            }}
            
            #dialogButton[primary="true"] {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {icon_color}, stop:1 {self._adjust_color(icon_color, -20)});
                color: #FFFFFF;
                border: none;
                font-weight: 700;
            }}
            
            #dialogButton[primary="true"]:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self._adjust_color(icon_color, 10)}, stop:1 {self._adjust_color(icon_color, -10)});
                color: #FFFFFF;
            }}
            
            #dialogButton[primary="true"]:pressed {{
                background: {self._adjust_color(icon_color, -30)};
                color: #FFFFFF;
            }}
        """
        )

    def _adjust_color(self, hex_color, amount):
        """Adjust hex color brightness"""
        # Remove # if present
        hex_color = hex_color.lstrip("#")

        # Convert to RGB
        r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

        # Adjust
        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))

        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Escape:
            self.button_result = self.buttons_config[
                -1
            ]  # Last button (usually No/Cancel)
            self.close_animated(QDialog.DialogCode.Rejected)
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.button_result = self.buttons_config[0]  # First button (usually Yes/OK)
            self.close_animated(QDialog.DialogCode.Accepted)
        else:
            super().keyPressEvent(event)

    def get_result(self):
        """Get which button was clicked"""
        return self.button_result

    @staticmethod
    def information(parent, title, message, detailed_text=""):
        """Show information dialog"""
        dialog = ModernMessageBox(
            parent=parent,
            message_type=ModernMessageBox.INFORMATION,
            title=title,
            message=message,
            detailed_text=detailed_text,
            buttons=["OK"],
        )
        dialog.show_animated()
        dialog.exec()
        return dialog.get_result()

    @staticmethod
    def warning(parent, title, message, detailed_text=""):
        """Show warning dialog"""
        dialog = ModernMessageBox(
            parent=parent,
            message_type=ModernMessageBox.WARNING,
            title=title,
            message=message,
            detailed_text=detailed_text,
            buttons=["OK"],
        )
        dialog.show_animated()
        dialog.exec()
        return dialog.get_result()

    @staticmethod
    def error(parent, title, message, detailed_text=""):
        """Show error dialog"""
        dialog = ModernMessageBox(
            parent=parent,
            message_type=ModernMessageBox.ERROR,
            title=title,
            message=message,
            detailed_text=detailed_text,
            buttons=["OK"],
        )
        dialog.show_animated()
        dialog.exec()
        return dialog.get_result()

    @staticmethod
    def success(parent, title, message, detailed_text=""):
        """Show success dialog"""
        dialog = ModernMessageBox(
            parent=parent,
            message_type=ModernMessageBox.SUCCESS,
            title=title,
            message=message,
            detailed_text=detailed_text,
            buttons=["OK"],
        )
        dialog.show_animated()
        dialog.exec()
        return dialog.get_result()

    @staticmethod
    def question(
        parent, title, message, detailed_text="", yes_text="Yes", no_text="No"
    ):
        """Show question dialog"""
        dialog = ModernMessageBox(
            parent=parent,
            message_type=ModernMessageBox.QUESTION,
            title=title,
            message=message,
            detailed_text=detailed_text,
            buttons=[yes_text, no_text],
        )
        dialog.show_animated()
        dialog.exec()

        return dialog.get_result() == yes_text


class ModernConfirmDialog(ModernMessageBox):
    """
    Specialized confirmation dialog
    Perfect for logout, delete, etc.
    """

    def __init__(
        self,
        parent=None,
        title="Confirm",
        message="Are you sure?",
        confirm_text="Yes",
        cancel_text="No",
        danger_mode=False,
    ):
        self.danger_mode = danger_mode
        super().__init__(
            parent=parent,
            message_type=self.WARNING if danger_mode else self.QUESTION,
            title=title,
            message=message,
            buttons=[confirm_text, cancel_text],
        )

    @staticmethod
    def confirm(
        parent, title, message, confirm_text="Yes", cancel_text="No", danger=False
    ):
        """Show confirmation dialog"""
        dialog = ModernConfirmDialog(
            parent=parent,
            title=title,
            message=message,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            danger_mode=danger,
        )
        dialog.show_animated()
        dialog.exec()

        return dialog.get_result() == confirm_text


class ModernNotification(QDialog):
    """
    Auto-dismissing notification toast
    Perfect for quick feedback messages
    """

    def __init__(self, parent=None, message="", message_type="info", duration=3000):
        super().__init__(parent)
        self.message = message
        self.message_type = message_type
        self.duration = duration

        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        """Setup notification UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Container
        container = QFrame()
        container.setObjectName("notificationContainer")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(20, 15, 20, 15)
        container_layout.setSpacing(12)

        # Icon
        icon = QLabel(self._get_icon())
        icon.setObjectName("notificationIcon")
        icon.setFont(QFont("Segoe UI", 16))

        # Message
        message_label = QLabel(self.message)
        message_label.setObjectName("notificationMessage")
        message_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        message_label.setWordWrap(True)

        container_layout.addWidget(icon)
        container_layout.addWidget(message_label, 1)

        layout.addWidget(container)

        # Set fixed width
        self.setFixedWidth(350)

    def _get_icon(self):
        """Get icon for notification type"""
        icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
        return icons.get(self.message_type, "ℹ️")

    def _get_color(self):
        """Get color for notification type"""
        colors = {
            "info": "#2196F3",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336",
        }
        return colors.get(self.message_type, "#2196F3")

    def apply_styles(self):
        """Apply notification styles with better contrast"""
        color = self._get_color()

        self.setStyleSheet(
            f"""
            #notificationContainer {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #F9FAFB);
                border-left: 5px solid {color};
                border: 1px solid #E5E7EB;
                border-radius: 14px;
            }}
            
            #notificationIcon {{
                color: {color};
                font-size: 20px;
                padding: 2px;
            }}
            
            #notificationMessage {{
                color: #1F2937;
                font-weight: 600;
                font-size: 13px;
            }}
        """
        )

    def show_notification(self):
        """Show notification with animation"""
        # Position at top-right of parent or screen
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.right() - self.width() - 20
            y = parent_rect.top() + 20
        else:
            from PyQt6.QtWidgets import QApplication

            screen = QApplication.primaryScreen().geometry()
            x = screen.right() - self.width() - 20
            y = screen.top() + 20

        self.move(x, y)

        # Apply opacity to layout widget, not dialog itself
        self.opacity_effect = QGraphicsOpacityEffect()
        container = self.findChild(QFrame, "notificationContainer")
        if container:
            container.setGraphicsEffect(self.opacity_effect)

            # Fade in
            self.opacity_effect.setOpacity(0)
            self.show()

            self.fade_in_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.fade_in_anim.setDuration(200)
            self.fade_in_anim.setStartValue(0)
            self.fade_in_anim.setEndValue(1)
            self.fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.fade_in_anim.start()
        else:
            self.show()

        # Auto dismiss
        QTimer.singleShot(self.duration, self.dismiss_notification)

    def dismiss_notification(self):
        """Dismiss notification with fade out"""
        if self.opacity_effect:
            self.fade_out_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.fade_out_anim.setDuration(200)
            self.fade_out_anim.setStartValue(1)
            self.fade_out_anim.setEndValue(0)
            self.fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
            self.fade_out_anim.finished.connect(self.close)
            self.fade_out_anim.start()
        else:
            self.close()

    @staticmethod
    def show(parent, message, message_type="info", duration=3000):
        """Show notification toast"""
        notification = ModernNotification(parent, message, message_type, duration)
        notification.show_notification()
        return notification
