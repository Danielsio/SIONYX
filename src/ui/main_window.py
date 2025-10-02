"""
Main Application Window - Placeholder
"""

from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class MainWindow(QMainWindow):
    """Main application window (placeholder for now)"""

    def __init__(self, auth_service, config):
        super().__init__()
        self.auth_service = auth_service
        self.config = config
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Sionyx - Dashboard")
        self.setMinimumSize(900, 600)

        # Center widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Success message
        success_label = QLabel("✅ Login Successful!")
        success_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        success_label.setStyleSheet("color: #4CAF50;")
        success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Dashboard will be built next")
        subtitle.setFont(QFont("Arial", 16))
        subtitle.setStyleSheet("color: #666;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        user_info = QLabel(f"Welcome, {self.auth_service.current_user.get('firstName', 'User')}!")
        user_info.setFont(QFont("Arial", 14))
        user_info.setStyleSheet("color: #333; margin-top: 20px;")
        user_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(success_label)
        layout.addWidget(subtitle)
        layout.addWidget(user_info)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
        """)