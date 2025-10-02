import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from services.auth_service import AuthService
from utils.config import Config


class SionyxApp:
    def __init__(self):
        self.login_window = None
        self.main_window = None
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Sionyx")
        self.app.setOrganizationName("Sionyx")

        # Enable high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

        self.config = Config()
        self.auth_service = AuthService(self.config)

        # Check if user is already logged in
        if self.auth_service.is_logged_in():
            self.show_main_window()
        else:
            self.show_login_window()

    def show_login_window(self):
        self.login_window = LoginWindow(self.auth_service)
        self.login_window.login_success.connect(self.show_main_window)
        self.login_window.show()

    def show_main_window(self):
        if hasattr(self, 'login_window'):
            self.login_window.close()

        self.main_window = MainWindow(self.auth_service, self.config)
        self.main_window.show()

    def run(self):
        return self.app.exec()


if __name__ == "__main__":
    app = SionyxApp()
    sys.exit(app.run())