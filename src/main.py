"""
SIONYX Desktop Application
Main entry point - Refactored for better error handling and constants usage
"""

import sys
from pathlib import Path

# Ensure src directory is in Python path
if __name__ == "__main__":
    src_dir = Path(__file__).parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

# CRITICAL: Import and configure WebEngine BEFORE QApplication
from PyQt6.QtCore import Qt, QCoreApplication
QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

# Now initialize logging
from utils.logger import SionyxLogger
from utils.const import APP_NAME
from ui.constants.ui_constants import UIStrings, Timing
import logging

SionyxLogger.setup(
    log_level=logging.INFO,
    log_to_file=True,
    enable_colors=True
)

SionyxLogger.cleanup_old_logs(days_to_keep=7)

from utils.logger import get_logger, set_context, generate_request_id
logger = get_logger(__name__)

from PyQt6.QtWidgets import QApplication, QInputDialog, QLineEdit
from ui.auth_window import AuthWindow
from ui.main_window import MainWindow
from services.auth_service import AuthService
from services.global_hotkey_service import GlobalHotkeyService
from utils.firebase_config import FirebaseConfig


class SionyxApp:
    """Main application class"""

    def __init__(self):
        # Generate request ID for this application session
        request_id = generate_request_id()
        set_context(request_id=request_id)
        
        logger.info("Initializing application", request_id=request_id, component="main_app")

        self.auth_window = None
        self.main_window = None
        self.global_hotkey_service = None

        try:
            # Enable high DPI scaling BEFORE creating QApplication
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
            
            # Create QApplication
            self.app = QApplication(sys.argv)
            self.app.setApplicationName(APP_NAME)
            self.app.setOrganizationName(APP_NAME)

            # Initialize services
            self.config = FirebaseConfig()
            self.auth_service = AuthService(self.config)

            # Initialize global hotkey service
            self.global_hotkey_service = GlobalHotkeyService()
            self.global_hotkey_service.admin_exit_requested.connect(self.handle_admin_exit)
            self.global_hotkey_service.start()

            # Show appropriate window
            if self.auth_service.is_logged_in():
                logger.info("User session restored", action="session_restore")
                self.show_main_window()
            else:
                logger.info("No active session", action="show_auth")
                self.show_auth_window()

        except Exception as e:
            logger.exception("Application initialization failed", error=str(e), component="main_app")
            raise

    def show_auth_window(self):
        """Display authentication window"""
        logger.info("Opening auth window", action="show_auth_window")
        self.auth_window = AuthWindow(self.auth_service)
        self.auth_window.login_success.connect(self.show_main_window)
        self.auth_window.show()

    def show_main_window(self):
        """Display main dashboard"""
        logger.info("Opening main dashboard", action="show_main_window")

        if self.auth_window is not None:
            self.auth_window.close()
            self.auth_window = None

        self.main_window = MainWindow(self.auth_service, self.config)
        self.main_window.show()

    def handle_admin_exit(self):
        """Handle global admin exit hotkey"""
        logger.warning("Admin exit hotkey triggered", action="admin_exit_attempt")
        
        # Show password dialog - use a more reliable approach
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
        
        dialog = QDialog()
        dialog.setWindowTitle("Administrator Access")
        dialog.setModal(True)
        
        # Set window flags to ensure it appears on top
        dialog.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        # Create layout
        layout = QVBoxLayout(dialog)
        
        # Label using constants
        label = QLabel("Enter administrator password to exit:")
        label.setStyleSheet(f"""
            QLabel {{
                color: #212121;
                font-size: 14px;
                font-weight: 600;
                padding: 10px;
            }}
        """)
        
        # Password input using constants
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 14px;
                border: 2px solid #1976D2;
                border-radius: 10px;
                background-color: #FAFAFA;
                color: #212121;
                font-size: 14px;
                min-width: 300px;
            }}
        """)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
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
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        
        # Connect buttons
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # Add to layout
        layout.addWidget(label)
        layout.addWidget(password_input)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Set dialog style
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #1976D2;
                border-radius: 10px;
            }
        """)
        
        # Center the dialog
        dialog.resize(400, 150)
        dialog.move(
            QApplication.primaryScreen().geometry().center() - dialog.rect().center()
        )
        
        # Show and focus
        dialog.show()
        dialog.activateWindow()
        dialog.raise_()
        password_input.setFocus()

        ok = dialog.exec()
        password = password_input.text()

        if ok and password == "admin123":
            # Try to end any active session gracefully first
            try:
                if self.main_window and hasattr(self.main_window, 'session_service'):
                    if self.main_window.session_service.is_session_active():
                        logger.info("Ending active session before admin exit", action="session_end", reason="admin_exit")
                        self.main_window.session_service.end_session('admin_exit')
            except Exception as e:
                logger.warning("Could not end session gracefully", error=str(e), action="admin_exit")

            # Force quit application
            logger.info("Force quitting application", action="admin_exit")
            self.cleanup()
            self.app.quit()
            sys.exit(0)
        elif ok:
            # Show error message for wrong password
            logger.warning("Incorrect admin password", action="admin_exit_failed")
            from PyQt6.QtWidgets import QMessageBox
            
            error_msg = QMessageBox()
            error_msg.setWindowTitle("Access Denied")
            error_msg.setText("Incorrect administrator password")
            error_msg.setIcon(QMessageBox.Icon.Warning)
            error_msg.setWindowFlags(
                Qt.WindowType.Dialog |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.WindowSystemMenuHint |
                Qt.WindowType.WindowCloseButtonHint
            )
            error_msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                    border: 2px solid #F44336;
                    border-radius: 10px;
                }
                QMessageBox QLabel {
                    color: #212121;
                    font-size: 14px;
                    font-weight: 600;
                }
                QMessageBox QPushButton {
                    background-color: #F44336;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: 600;
                    min-width: 80px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #D32F2F;
                }
            """)
            error_msg.exec()

    def cleanup(self):
        """Cleanup resources before exit"""
        try:
            if self.global_hotkey_service:
                self.global_hotkey_service.stop()
        except Exception as e:
            logger.warning("Error during cleanup", error=str(e), action="cleanup")

    def run(self):
        """Start application event loop"""
        logger.info("Starting event loop", action="start_event_loop")
        try:
            return self.app.exec()
        finally:
            self.cleanup()


if __name__ == "__main__":
    try:
        app = SionyxApp()
        exit_code = app.run()
        logger.info("Application exited cleanly", exit_code=exit_code, action="app_exit")
        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.warning("Application interrupted by user", action="keyboard_interrupt")
        sys.exit(0)

    except Exception as e:
        logger.critical("Fatal error - application crashed", error=str(e), action="fatal_error")
        logger.exception("Fatal error details")
        sys.exit(1)