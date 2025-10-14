"""
Base Window - Shared functionality for all fullscreen kiosk windows
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication, QInputDialog, QLineEdit
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QKeySequence, QShortcut

from ui.styles import BASE_QSS
from ui.modern_dialogs import ModernMessageBox, ModernConfirmDialog, ModernNotification

class BaseKioskWindow(QWidget):
    """Base class for fullscreen kiosk windows"""

    def __init__(self):
        super().__init__()
        self.setup_kiosk_window()

    def setup_kiosk_window(self):
        """Setup fullscreen kiosk mode - common to all windows"""
        # Frameless, always on top
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # Fullscreen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.showFullScreen()

        # Modal
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Admin exit shortcut
        self.exit_shortcut = QShortcut(QKeySequence("Ctrl+Alt+Q"), self)
        self.exit_shortcut.activated.connect(self.admin_exit)

        # Prevent closing
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

    def create_main_layout(self):
        """Create standard main layout with no margins"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        return main_layout

    def admin_exit(self):
        """Admin exit with password - FORCE closes entire application"""
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Administrator Access")
        dialog.setLabelText("Enter administrator password to exit:")
        dialog.setTextEchoMode(QLineEdit.EchoMode.Password)
        dialog.setStyleSheet("""
            QInputDialog {
                background-color: white;
            }
            QLabel {
                color: #212121;
                font-size: 14px;
                font-weight: 600;
                padding: 10px;
            }
            QLineEdit {
                padding: 14px;
                border: 2px solid #1976D2;
                border-radius: 10px;
                background-color: #FAFAFA;
                color: #212121;
                font-size: 14px;
                min-width: 300px;
            }
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)

        ok = dialog.exec()
        password = dialog.textValue()

        if ok and password == "admin123":
            # Force close ALL windows and exit application immediately
            import sys

            # Close all windows
            for widget in QApplication.topLevelWidgets():
                widget.close()

            # Force quit application
            QApplication.quit()

            # Nuclear option - force exit the Python process
            sys.exit(0)

        elif ok:
            ModernMessageBox.error(
                self,
                "Access Denied",
                "Incorrect administrator password"
            )

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
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(400)

        geometry = widget.geometry()

        animation.setKeyValueAt(0, geometry)
        animation.setKeyValueAt(0.1, geometry.translated(-8, 0))
        animation.setKeyValueAt(0.2, geometry.translated(8, 0))
        animation.setKeyValueAt(0.3, geometry.translated(-8, 0))
        animation.setKeyValueAt(0.4, geometry.translated(8, 0))
        animation.setKeyValueAt(0.5, geometry.translated(-4, 0))
        animation.setKeyValueAt(0.6, geometry.translated(4, 0))
        animation.setKeyValueAt(0.7, geometry)

        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        animation.start()

    def show_error(self, title: str, message: str, detailed_text: str = ""):
        """Show modern error message"""
        ModernMessageBox.error(self, title, message, detailed_text)

    def show_success(self, title: str, message: str, detailed_text: str = ""):
        """Show modern success message"""
        ModernMessageBox.success(self, title, message, detailed_text)
    
    def show_warning(self, title: str, message: str, detailed_text: str = ""):
        """Show modern warning message"""
        ModernMessageBox.warning(self, title, message, detailed_text)
    
    def show_info(self, title: str, message: str, detailed_text: str = ""):
        """Show modern information message"""
        ModernMessageBox.information(self, title, message, detailed_text)
    
    def show_question(self, title: str, message: str, detailed_text: str = "", 
                     yes_text: str = "Yes", no_text: str = "No"):
        """Show modern question dialog, returns True if Yes clicked"""
        return ModernMessageBox.question(self, title, message, detailed_text, yes_text, no_text)
    
    def show_confirm(self, title: str, message: str, confirm_text: str = "Yes", 
                    cancel_text: str = "No", danger: bool = False):
        """Show modern confirmation dialog, returns True if confirmed"""
        return ModernConfirmDialog.confirm(self, title, message, confirm_text, cancel_text, danger)
    
    def show_notification(self, message: str, message_type: str = "info", duration: int = 3000):
        """Show auto-dismissing notification toast"""
        return ModernNotification.show(self, message, message_type, duration)

    def apply_base_stylesheet(self):
        """Apply base stylesheet - consistent across all windows"""
        return BASE_QSS