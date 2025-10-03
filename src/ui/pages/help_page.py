"""
Help & Support Page
Contact info and FAQs
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from utils.logger import get_logger

logger = get_logger(__name__)


class HelpPage(QWidget):
    """Help and support page"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.current_user = auth_service.get_current_user()

        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setObjectName("contentPage")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(45, 35, 45, 35)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Help & Support")
        title.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        title.setStyleSheet("color: #1A1A1A;")

        subtitle = QLabel("Get assistance and find answers to common questions")
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setStyleSheet("color: #6B7280; margin-bottom: 25px;")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()

        logger.debug("Help page initialized")