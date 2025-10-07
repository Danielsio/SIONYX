"""
Modern, Beautiful Dialog System
Professional UI/UX for all app dialogs
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFrame, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QIcon


class ModernDialog(QDialog):
    """Base class for modern, beautiful dialogs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Animation setup
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        """Setup the basic UI structure"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Dark overlay background
        self.overlay = QFrame()
        self.overlay.setObjectName("dialogOverlay")
        overlay_layout = QVBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container with shadow effect
        self.container = QFrame()
        self.container.setObjectName("dialogContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(35, 35, 35, 35)
        
        overlay_layout.addWidget(self.container)
        main_layout.addWidget(self.overlay)
        
    def apply_styles(self):
        """Apply modern styling with better contrast"""
        self.setStyleSheet("""
            QDialog {
                background: rgba(0, 0, 0, 180);
            }
            
            #dialogOverlay {
                background: transparent;
            }
            
            #dialogContainer {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF,
                    stop:1 #F5F7FA
                );
                border-radius: 24px;
                border: 3px solid rgba(255, 255, 255, 0.8);
                /* Outer glow for depth */
                padding: 2px;
            }
        """)
        
    def show_animated(self):
        """Show dialog with fade-in animation"""
        self.opacity_effect.setOpacity(0)
        self.show()
        
        # Fade in animation
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(200)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_in.start()
        
    def close_animated(self, result=None):
        """Close dialog with fade-out animation"""
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
    
    def __init__(self, parent=None, message_type=INFORMATION, title="", message="", 
                 detailed_text="", buttons=None):
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
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
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
            
            btn.clicked.connect(lambda checked, text=button_text: self._button_clicked(text))
            buttons_layout.addWidget(btn)
        
        container_layout.addLayout(buttons_layout)
        
        # Set fixed width for better appearance
        self.setFixedWidth(500)
        
    def _get_icon_emoji(self):
        """Get emoji icon based on message type"""
        icons = {
            self.INFORMATION: "ℹ️",
            self.WARNING: "⚠️",
            self.ERROR: "❌",
            self.SUCCESS: "✅",
            self.QUESTION: "❓"
        }
        return icons.get(self.message_type, "ℹ️")
    
    def _get_icon_color(self):
        """Get color based on message type"""
        colors = {
            self.INFORMATION: "#2196F3",
            self.WARNING: "#FF9800",
            self.ERROR: "#F44336",
            self.SUCCESS: "#4CAF50",
            self.QUESTION: "#9C27B0"
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
        
        self.setStyleSheet(self.styleSheet() + f"""
            #dialogIcon {{
                font-size: 44px;
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {icon_color}30,
                    stop:1 {icon_color}15
                );
                border: 2px solid {icon_color}40;
                border-radius: 26px;
            }}
            
            #dialogTitle {{
                color: #1a1a1a;
                padding-top: 5px;
                font-weight: bold;
            }}
            
            #dialogMessage {{
                color: #2c3e50;
                line-height: 1.7;
                font-size: 14px;
            }}
            
            #dialogDetailed {{
                color: #34495e;
                line-height: 1.6;
                padding: 16px;
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa,
                    stop:1 #e9ecef
                );
                border: 1px solid #dee2e6;
                border-radius: 12px;
                margin-top: 8px;
            }}
            
            #dialogButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e9ecef,
                    stop:1 #dee2e6
                );
                color: #495057;
                border: 2px solid #ced4da;
                border-radius: 24px;
                padding: 14px 32px;
                font-size: 15px;
                font-weight: 700;
                min-width: 120px;
            }}
            
            #dialogButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dee2e6,
                    stop:1 #ced4da
                );
                border: 2px solid #adb5bd;
            }}
            
            #dialogButton:pressed {{
                background: #ced4da;
                border: 2px solid #6c757d;
            }}
            
            #dialogButton[primary="true"] {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {self._adjust_color(icon_color, 15)},
                    stop:1 {icon_color}
                );
                color: white;
                border: 2px solid {self._adjust_color(icon_color, -20)};
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
                font-weight: 700;
            }}
            
            #dialogButton[primary="true"]:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 {icon_color},
                    stop:1 {self._adjust_color(icon_color, -15)}
                );
                border: 2px solid {self._adjust_color(icon_color, -30)};
            }}
            
            #dialogButton[primary="true"]:pressed {{
                background: {self._adjust_color(icon_color, -20)};
                border: 2px solid {self._adjust_color(icon_color, -40)};
            }}
        """)
    
    def _adjust_color(self, hex_color, amount):
        """Adjust hex color brightness"""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Adjust
        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))
        
        # Convert back to hex
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Escape:
            self.button_result = self.buttons_config[-1]  # Last button (usually No/Cancel)
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
            buttons=["OK"]
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
            buttons=["OK"]
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
            buttons=["OK"]
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
            buttons=["OK"]
        )
        dialog.show_animated()
        dialog.exec()
        return dialog.get_result()
    
    @staticmethod
    def question(parent, title, message, detailed_text="", yes_text="Yes", no_text="No"):
        """Show question dialog"""
        dialog = ModernMessageBox(
            parent=parent,
            message_type=ModernMessageBox.QUESTION,
            title=title,
            message=message,
            detailed_text=detailed_text,
            buttons=[yes_text, no_text]
        )
        dialog.show_animated()
        result = dialog.exec()
        
        return dialog.get_result() == yes_text


class ModernConfirmDialog(ModernMessageBox):
    """
    Specialized confirmation dialog
    Perfect for logout, delete, etc.
    """
    
    def __init__(self, parent=None, title="Confirm", message="Are you sure?", 
                 confirm_text="Yes", cancel_text="No", danger_mode=False):
        self.danger_mode = danger_mode
        super().__init__(
            parent=parent,
            message_type=self.WARNING if danger_mode else self.QUESTION,
            title=title,
            message=message,
            buttons=[confirm_text, cancel_text]
        )
    
    @staticmethod
    def confirm(parent, title, message, confirm_text="Yes", cancel_text="No", danger=False):
        """Show confirmation dialog"""
        dialog = ModernConfirmDialog(
            parent=parent,
            title=title,
            message=message,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            danger_mode=danger
        )
        dialog.show_animated()
        result = dialog.exec()
        
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
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
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
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        return icons.get(self.message_type, "ℹ️")
    
    def _get_color(self):
        """Get color for notification type"""
        colors = {
            "info": "#2196F3",
            "success": "#4CAF50",
            "warning": "#FF9800",
            "error": "#F44336"
        }
        return colors.get(self.message_type, "#2196F3")
    
    def apply_styles(self):
        """Apply notification styles with better contrast"""
        color = self._get_color()
        
        self.setStyleSheet(f"""
            #notificationContainer {{
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff,
                    stop:1 #f8f9fa
                );
                border-left: 5px solid {color};
                border: 2px solid {color}40;
                border-left: 5px solid {color};
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
            }}
            
            #notificationIcon {{
                color: {color};
                font-size: 18px;
            }}
            
            #notificationMessage {{
                color: #1a1a1a;
                font-weight: 600;
            }}
        """)
    
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
        
        # Opacity animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        # Fade in
        self.opacity_effect.setOpacity(0)
        self.show()
        
        fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_in.setDuration(200)
        fade_in.setStartValue(0)
        fade_in.setEndValue(1)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade_in.start()
        
        # Auto dismiss
        QTimer.singleShot(self.duration, self.dismiss_notification)
    
    def dismiss_notification(self):
        """Dismiss notification with fade out"""
        fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        fade_out.finished.connect(self.close)
        fade_out.start()
    
    @staticmethod
    def show(parent, message, message_type="info", duration=3000):
        """Show notification toast"""
        notification = ModernNotification(parent, message, message_type, duration)
        notification.show_notification()
        return notification

