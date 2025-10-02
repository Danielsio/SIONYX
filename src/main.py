"""
Sionyx Desktop Application
Main entry point
"""

import sys
from pathlib import Path

# Ensure src directory is in Python path
# This makes imports work whether run from IDE or command line
if __name__ == "__main__":
    src_dir = Path(__file__).parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from services.auth_service import AuthService
from utils.firebase_config import FirebaseConfig


class SionyxApp:
    """Main application class"""

    def __init__(self):
        self.login_window = None
        self.main_window = None

        # Create QApplication
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Sionyx")
        self.app.setOrganizationName("Sionyx")

        # Enable high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        # Initialize services1
        self.config = FirebaseConfig()
        self.auth_service = AuthService(self.config)

        # Show appropriate window based on login state
        if self.auth_service.is_logged_in():
            self.show_main_window()
        else:
            self.show_login_window()

    def show_login_window(self):
        """Display login window"""
        self.login_window = LoginWindow(self.auth_service)
        self.login_window.login_success.connect(self.show_main_window)
        self.login_window.show()

    def show_main_window(self):
        """Display main dashboard window"""
        # Close login window if it exists
        if self.login_window is not None:
            self.login_window.close()
            self.login_window = None

        # Create and show main window
        self.main_window = MainWindow(self.auth_service, self.config)
        self.main_window.show()

    def run(self):
        """Start the application event loop"""
        return self.app.exec()


if __name__ == "__main__":
    app = SionyxApp()
    sys.exit(app.run())