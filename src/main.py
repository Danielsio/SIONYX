"""
Sionyx Desktop Application
Main entry point
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
import logging

SionyxLogger.setup(
    log_level=logging.INFO,
    log_to_file=True,
    enable_colors=True
)

SionyxLogger.cleanup_old_logs(days_to_keep=7)

from utils.logger import get_logger
logger = get_logger(__name__)

from PyQt6.QtWidgets import QApplication
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from services.auth_service import AuthService
from utils.firebase_config import FirebaseConfig


class SionyxApp:
    """Main application class"""

    def __init__(self):
        logger.info("Initializing application components")

        self.login_window = None
        self.main_window = None

        try:
            # Create QApplication
            self.app = QApplication(sys.argv)
            self.app.setApplicationName("Sionyx")
            self.app.setOrganizationName("Sionyx")
            logger.debug("Qt Application created")

            # Enable high DPI scaling
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
            logger.debug("High DPI scaling enabled")

            # Initialize services
            self.config = FirebaseConfig()
            logger.debug("Configuration loaded")

            self.auth_service = AuthService(self.config)
            logger.debug("Authentication service initialized")

            # Show appropriate window
            if self.auth_service.is_logged_in():
                logger.info("User session restored from cache")
                self.show_main_window()
            else:
                logger.info("No active session, showing login screen")
                self.show_login_window()

        except Exception as e:
            logger.exception("Failed to initialize application")
            raise

    def show_login_window(self):
        """Display login window"""
        logger.info("Opening login window")
        self.login_window = LoginWindow(self.auth_service)
        self.login_window.login_success.connect(self.show_main_window)
        self.login_window.show()
        logger.debug("Login window displayed")

    def show_main_window(self):
        """Display main dashboard"""
        logger.info("Opening main dashboard")

        if self.login_window is not None:
            self.login_window.close()
            self.login_window = None
            logger.debug("Login window closed")

        self.main_window = MainWindow(self.auth_service, self.config)
        self.main_window.show()
        logger.debug("Main dashboard displayed")

    def run(self):
        """Start application event loop"""
        logger.info("Starting event loop")
        return self.app.exec()


if __name__ == "__main__":
    try:
        app = SionyxApp()
        exit_code = app.run()
        logger.info(f"Application exited cleanly (code: {exit_code})")
        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.warning("Application interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.critical("Fatal error - application crashed")
        logger.exception(e)
        sys.exit(1)