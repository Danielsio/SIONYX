"""
SIONYX Desktop Application
Main entry point - Refactored for better error handling and constants usage
"""

import argparse
import logging
import sys
from pathlib import Path


# Add project root to Python path BEFORE any imports
# This allows imports like "from services..." to work regardless of how the script is run
if __name__ == "__main__":
    # Get the project root directory (parent of src)
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from PyQt6.QtCore import QCoreApplication, Qt
from PyQt6.QtWidgets import QApplication, QLineEdit, QMessageBox

from services.auth_service import AuthService
from services.global_hotkey_service import GlobalHotkeyService
from services.keyboard_restriction_service import KeyboardRestrictionService
from services.process_restriction_service import ProcessRestrictionService
from ui.auth_window import AuthWindow
from ui.main_window import MainWindow
from utils.const import ADMIN_EXIT_PASSWORD, APP_NAME
from utils.firebase_config import get_firebase_config
from utils.logger import (
    SionyxLogger,
    generate_request_id,
    get_logger,
    set_context,
)


# CRITICAL: Import and configure WebEngine BEFORE QApplication
QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

# Set up logging with appropriate level
log_level = (
    logging.DEBUG if "--verbose" in sys.argv or "-v" in sys.argv else logging.INFO
)
SionyxLogger.setup(log_level=log_level, log_to_file=True, enable_colors=True)

SionyxLogger.cleanup_old_logs(days_to_keep=7)

logger = get_logger(__name__)


class SionyxApp:
    """Main application class"""

    def __init__(self, verbose=False, kiosk_mode=False):
        # Generate request ID for this application session
        request_id = generate_request_id()
        set_context(request_id=request_id)

        # Store command line options
        self.verbose = verbose
        self.kiosk_mode = kiosk_mode

        logger.info(
            "Initializing application",
            request_id=request_id,
            component="main_app",
            verbose=verbose,
            kiosk_mode=kiosk_mode,
        )

        self.auth_window = None
        self.main_window = None
        self.global_hotkey_service = None
        self.keyboard_restriction_service = None
        self.process_restriction_service = None

        try:
            # Enable high DPI scaling BEFORE creating QApplication
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )

            # Create QApplication
            self.app = QApplication(sys.argv)
            self.app.setApplicationName(APP_NAME)
            self.app.setOrganizationName(APP_NAME)

            # Set application icon (for taskbar on Windows)
            from PyQt6.QtGui import QIcon

            from ui.base_window import get_app_icon_path

            icon_path = get_app_icon_path()
            if icon_path:
                self.app.setWindowIcon(QIcon(icon_path))
                logger.debug(f"Application icon set from: {icon_path}")

            # Check configuration exists before starting
            # Production: Uses Windows Registry (set by installer)
            # Development: Uses .env file
            if not getattr(sys, "frozen", False):
                # Development mode - check .env file exists
                repo_root = Path(__file__).parent.parent.parent
                env_path = repo_root / ".env"
                if not env_path.exists():
                    env_path = Path(".env")
                if not env_path.exists():
                    logger.error(
                        "No .env file found for development mode.",
                        action="missing_config",
                    )
                    QMessageBox.critical(
                        None,
                        "Configuration Missing",
                        "SIONYX configuration file (.env) not found.\n\n"
                        "Create a .env file in the project root with:\n"
                        "- FIREBASE_API_KEY\n"
                        "- FIREBASE_DATABASE_URL\n"
                        "- FIREBASE_PROJECT_ID\n"
                        "- ORG_ID",
                    )
                    self.app.quit()
                    sys.exit(1)
            else:
                # Production mode - check registry config exists
                from utils.registry_config import registry_config_exists

                if not registry_config_exists():
                    logger.error(
                        "Registry configuration not found. Please reinstall.",
                        action="missing_registry_config",
                    )
                    QMessageBox.critical(
                        None,
                        "Configuration Missing",
                        "SIONYX configuration not found in Windows Registry.\n\n"
                        "Please reinstall the application to fix this issue.\n\n"
                        "If this problem persists, contact your system administrator.",
                    )
                    self.app.quit()
                    sys.exit(1)

            # Initialize services
            self.config = get_firebase_config()
            self.auth_service = AuthService(self.config)

            # Initialize global hotkey service
            self.global_hotkey_service = GlobalHotkeyService()
            # IMPORTANT: Use QueuedConnection because the signal is emitted from
            # a background thread (keyboard listener), but GUI operations must
            # run on the main thread
            self.global_hotkey_service.admin_exit_requested.connect(
                self.handle_admin_exit, Qt.ConnectionType.QueuedConnection
            )
            self.global_hotkey_service.start()
            logger.info("Global hotkey service started (Ctrl+Alt+Q for admin exit)")

            # Initialize kiosk security services if in kiosk mode
            if self.kiosk_mode:
                logger.info("Kiosk mode enabled - starting security services")
                self._start_kiosk_services()

            # Show appropriate window
            if self.auth_service.is_logged_in():
                logger.info("User session restored", action="session_restore")
                self.show_main_window()
            else:
                logger.info("No active session", action="show_auth")
                self.show_auth_window()

        except Exception as e:
            logger.exception(
                "Application initialization failed", error=str(e), component="main_app"
            )
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

        self.main_window = MainWindow(
            self.auth_service, self.config, kiosk_mode=self.kiosk_mode
        )
        self.main_window.show()

    def handle_admin_exit(self):
        """Handle global admin exit hotkey (Ctrl+Alt+Q)"""
        logger.warning(
            "Admin exit hotkey triggered on main thread",
            action="admin_exit_attempt",
            thread="main",
        )

        # Show password dialog - use a more reliable approach
        from PyQt6.QtWidgets import (
            QDialog,
            QHBoxLayout,
            QLabel,
            QPushButton,
            QVBoxLayout,
        )

        dialog = QDialog()
        dialog.setWindowTitle("Administrator Access")
        dialog.setModal(True)

        # Set window flags to ensure it appears on top
        dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        # Create layout
        layout = QVBoxLayout(dialog)

        # Label using constants
        label = QLabel("Enter administrator password to exit:")
        label.setStyleSheet(
            """
            QLabel {
                color: #212121;
                font-size: 14px;
                font-weight: 600;
                padding: 10px;
            }
        """
        )

        # Password input using constants
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_input.setStyleSheet(
            """
            QLineEdit {
                padding: 14px;
                border: 2px solid #1976D2;
                border-radius: 10px;
                background-color: #FAFAFA;
                color: #212121;
                font-size: 14px;
                min-width: 300px;
            }
        """
        )

        # Buttons
        button_layout = QHBoxLayout()

        ok_button = QPushButton("OK")
        ok_button.setStyleSheet(
            """
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
        """
        )

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(
            """
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
        """
        )

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
        dialog.setStyleSheet(
            """
            QDialog {
                background-color: white;
                border: 2px solid #1976D2;
                border-radius: 10px;
            }
        """
        )

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

        if ok and password == ADMIN_EXIT_PASSWORD:
            # Try to end any active session gracefully first
            try:
                if self.main_window and hasattr(self.main_window, "session_service"):
                    if self.main_window.session_service.is_session_active():
                        logger.info(
                            "Ending active session before admin exit",
                            action="session_end",
                            reason="admin_exit",
                        )
                        self.main_window.session_service.end_session("admin_exit")
            except Exception as e:
                logger.warning(
                    "Could not end session gracefully",
                    error=str(e),
                    action="admin_exit",
                )

            # Force quit application
            logger.info("Force quitting application", action="admin_exit")
            # Allow window to close in kiosk mode
            if self.main_window:
                self.main_window.allow_close()
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
                Qt.WindowType.Dialog
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.WindowSystemMenuHint
                | Qt.WindowType.WindowCloseButtonHint
            )
            error_msg.setStyleSheet(
                """
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
            """
            )
            error_msg.exec()

    def _start_kiosk_services(self):
        """Start kiosk security services (keyboard and process restrictions)."""
        try:
            # Keyboard restriction - blocks Alt+Tab, Win key, etc.
            self.keyboard_restriction_service = KeyboardRestrictionService(enabled=True)
            self.keyboard_restriction_service.blocked_key_pressed.connect(
                self._on_blocked_key
            )
            self.keyboard_restriction_service.start()
            logger.info("Keyboard restriction service started")

            # Process restriction - kills cmd, regedit, etc.
            self.process_restriction_service = ProcessRestrictionService(enabled=True)
            self.process_restriction_service.process_blocked.connect(
                self._on_blocked_process
            )
            self.process_restriction_service.start()
            logger.info("Process restriction service started")

        except Exception as e:
            logger.error(f"Failed to start kiosk services: {e}")

    def _on_blocked_key(self, combo_name: str):
        """Handle blocked key combination."""
        logger.warning(f"Blocked key combination: {combo_name}", action="key_blocked")

    def _on_blocked_process(self, process_name: str):
        """Handle blocked process."""
        logger.warning(f"Blocked process: {process_name}", action="process_blocked")

    def cleanup(self):
        """Cleanup resources before exit"""
        try:
            if self.global_hotkey_service:
                self.global_hotkey_service.stop()
            if self.keyboard_restriction_service:
                self.keyboard_restriction_service.stop()
            if self.process_restriction_service:
                self.process_restriction_service.stop()
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="SIONYX Desktop Application")
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )
    parser.add_argument(
        "--kiosk",
        "-k",
        action="store_true",
        help="Enable kiosk mode (block system keys, kill unauthorized processes)",
    )
    args = parser.parse_args()

    try:
        app = SionyxApp(verbose=args.verbose, kiosk_mode=args.kiosk)
        exit_code = app.run()
        logger.info(
            "Application exited cleanly", exit_code=exit_code, action="app_exit"
        )
        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.warning("Application interrupted by user", action="keyboard_interrupt")
        sys.exit(0)

    except Exception as e:
        logger.critical(
            "Fatal error - application crashed", error=str(e), action="fatal_error"
        )
        logger.exception("Fatal error details")
        sys.exit(1)
