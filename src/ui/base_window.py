"""
Base Window - Shared functionality for all fullscreen kiosk windows
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication, QMessageBox, QInputDialog, QLineEdit
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QKeySequence, QShortcut


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
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Access Denied")
            msg.setText("Incorrect administrator password")
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QLabel {
                    color: #D32F2F;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton {
                    background-color: #D32F2F;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 24px;
                    font-weight: 600;
                }
            """)
            msg.exec()

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

    def show_error(self, title: str, message: str):
        """Show standardized error message"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(f"<b style='color: #D32F2F;'>{message}</b>")
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QLabel {
                color: #212121;
                font-size: 13px;
            }
            QPushButton {
                background-color: #D32F2F;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #C62828;
            }
        """)
        msg.exec()

    def show_success(self, title: str, message: str):
        """Show standardized success message"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(title)
        msg.setText(f"<b style='color: #388E3C;'>{message}</b>")
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QLabel {
                color: #212121;
                font-size: 13px;
            }
            QPushButton {
                background-color: #388E3C;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #2E7D32;
            }
        """)
        msg.exec()

    def apply_base_stylesheet(self):
        """Apply base stylesheet - consistent across all windows"""
        return """
            /* Global font + background */
            * { font-family: 'Segoe UI'; }

            /* Main background gradient */
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #EAF3FE,
                    stop:0.5 #CFE6FD,
                    stop:1 #B9DBFC
                );
            }

            /* Card styling */
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E5E7EB;
            }

            /* Inputs */
            #inputField {
                padding: 14px 16px;
                border: 2px solid #CBD5E1;
                border-radius: 12px;
                background-color: #F8FAFC;
                color: #111827;
                font-size: 13px;
                selection-background-color: #1976D2;
                selection-color: white;
            }

            #inputField:hover { border: 2px solid #94A3B8; background-color: #FFFFFF; }
            #inputField:focus { border: 2px solid #2563EB; background-color: #FFFFFF; }
            #inputField::placeholder { color: #94A3B8; }

            /* Default button baseline (specific #ids override) */
            QPushButton {
                background-color: #FFFFFF;
                color: #111827;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 10px 16px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #F9FAFB; }
            QPushButton:pressed { background-color: #EFF1F5; }

            /* Primary button */
            #primaryButton {
                background-color: #1976D2;
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
                font-weight: 700;
                font-size: 14px;
                letter-spacing: 0.3px;
            }
            #primaryButton:hover { background-color: #1565C0; }
            #primaryButton:pressed { background-color: #0D47A1; }
            #primaryButton:disabled { background-color: #D1D5DB; color: #6B7280; }

            /* Scrollbars */
            QScrollBar:vertical { background: transparent; width: 10px; margin: 4px; }
            QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 5px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background: #94A3B8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

            QScrollBar:horizontal { background: transparent; height: 10px; margin: 4px; }
            QScrollBar::handle:horizontal { background: #CBD5E1; border-radius: 5px; min-width: 30px; }
            QScrollBar::handle:horizontal:hover { background: #94A3B8; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

            /* Tooltips */
            QToolTip {
                color: #111827;
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 6px 10px;
            }
        """