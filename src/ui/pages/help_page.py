"""
Help & Support Page
Contact info and FAQs
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QLabel, QVBoxLayout, QWidget

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

        # Set RTL layout direction for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(45, 35, 45, 35)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Create header matching history page style
        self.create_header(layout)
        layout.addStretch()

        logger.debug("Help page initialized")

    def create_header(self, parent_layout):
        """Create page header matching history page style"""
        # Clean header section matching history page style
        header_container = QWidget()
        header_container.setStyleSheet(
            """
            QWidget {
                background: #3B82F6;
                border-radius: 20px;
                padding: 20px;
            }
        """
        )

        # Add shadow to header - Enhanced shadow effect
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(50)
        header_shadow.setXOffset(0)
        header_shadow.setYOffset(15)
        header_shadow.setColor(QColor(0, 0, 0, 65))
        header_container.setGraphicsEffect(header_shadow)
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(30, 25, 30, 25)
        header_layout.setSpacing(8)

        # Main title with stunning typography
        title = QLabel("עזרה ותמיכה")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: 800;
                margin-bottom: 8px;
            }
        """
        )

        # Subtitle with elegant styling
        subtitle = QLabel("קבל עזרה ומצא תשובות לשאלות נפוצות")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            """
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                font-weight: 400;
            }
        """
        )

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        parent_layout.addWidget(header_container)
