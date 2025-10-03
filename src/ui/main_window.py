"""
Main Window - Modern Web-Style Navigation
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.base_window import BaseKioskWindow
from ui.pages.home_page import HomePage
from ui.pages.packages_page import PackagesPage
from ui.pages.history_page import HistoryPage
from ui.pages.help_page import HelpPage
from utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(BaseKioskWindow):
    """Main container with modern sidebar navigation"""

    PAGES = {
        'HOME': 0,
        'PACKAGES': 1,
        'HISTORY': 2,
        'HELP': 3
    }

    def __init__(self, auth_service, config):
        super().__init__()
        self.auth_service = auth_service
        self.config = config
        self.current_user = auth_service.get_current_user()

        self.page_names = {v: k for k, v in self.PAGES.items()}

        logger.info(f"Dashboard opened: {self.current_user.get('firstName')}")
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Sionyx - Dashboard")

        main_layout = self.create_main_layout()

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Modern sidebar
        sidebar = self.create_modern_sidebar()

        # Content stack
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentStack")

        # Create pages
        self.home_page = HomePage(self.auth_service, self)
        self.packages_page = PackagesPage(self.auth_service, self)
        self.history_page = HistoryPage(self.auth_service, self)
        self.help_page = HelpPage(self.auth_service, self)

        self.content_stack.addWidget(self.home_page)
        self.content_stack.addWidget(self.packages_page)
        self.content_stack.addWidget(self.history_page)
        self.content_stack.addWidget(self.help_page)

        container_layout.addWidget(sidebar)
        container_layout.addWidget(self.content_stack, 1)

        main_layout.addWidget(container)
        self.setLayout(main_layout)

        self.apply_modern_styles()
        self.show_page(self.PAGES['HOME'])

    def create_modern_sidebar(self) -> QWidget:
        """Create modern, clean sidebar like web apps"""
        sidebar = QFrame()
        sidebar.setObjectName("modernSidebar")
        sidebar.setFixedWidth(240)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top section - Logo + User
        top_section = QWidget()
        top_layout = QVBoxLayout(top_section)
        top_layout.setContentsMargins(20, 25, 20, 20)
        top_layout.setSpacing(20)

        # Logo
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(4)

        logo = QLabel("SIONYX")
        logo.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        logo.setStyleSheet("color: #111827;")

        tagline = QLabel("Time Management")
        tagline.setFont(QFont("Segoe UI", 9))
        tagline.setStyleSheet("color: #9CA3AF;")

        logo_layout.addWidget(logo)
        logo_layout.addWidget(tagline)

        # User info card
        user_card = QFrame()
        user_card.setObjectName("userCard")
        user_card_layout = QVBoxLayout(user_card)
        user_card_layout.setContentsMargins(12, 10, 12, 10)
        user_card_layout.setSpacing(2)

        user_name = QLabel(f"{self.current_user.get('firstName', 'User')}")
        user_name.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        user_name.setStyleSheet("color: #111827;")

        user_phone = QLabel(f"{self.current_user.get('phoneNumber', '')}")
        user_phone.setFont(QFont("Segoe UI", 9))
        user_phone.setStyleSheet("color: #6B7280;")

        user_card_layout.addWidget(user_name)
        user_card_layout.addWidget(user_phone)

        top_layout.addWidget(logo_container)
        top_layout.addWidget(user_card)

        # Navigation section
        nav_section = QWidget()
        nav_layout = QVBoxLayout(nav_section)
        nav_layout.setContentsMargins(12, 10, 12, 10)
        nav_layout.setSpacing(4)

        # Navigation label
        nav_label = QLabel("MENU")
        nav_label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        nav_label.setStyleSheet("color: #9CA3AF; padding-left: 8px; margin-bottom: 6px;")
        nav_layout.addWidget(nav_label)

        self.nav_buttons = []

        nav_items = [
            ("Home", self.PAGES['HOME']),
            ("Packages", self.PAGES['PACKAGES']),
            ("History", self.PAGES['HISTORY']),
            ("Help", self.PAGES['HELP'])
        ]

        for label, index in nav_items:
            btn = self.create_modern_nav_button(label, index)
            self.nav_buttons.append(btn)
            nav_layout.addWidget(btn)

        nav_layout.addStretch()

        # Bottom section - Logout
        bottom_section = QWidget()
        bottom_layout = QVBoxLayout(bottom_section)
        bottom_layout.setContentsMargins(12, 10, 12, 20)
        bottom_layout.setSpacing(0)

        btn_logout = QPushButton("Logout")
        btn_logout.setObjectName("modernLogoutButton")
        btn_logout.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        btn_logout.setMinimumHeight(40)
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.clicked.connect(self.handle_logout)
        bottom_layout.addWidget(btn_logout)

        # Add sections to sidebar
        layout.addWidget(top_section)
        layout.addWidget(nav_section, 1)
        layout.addWidget(bottom_section)

        return sidebar

    def create_modern_nav_button(self, text: str, page_index: int) -> QPushButton:
        """Create modern navigation button"""
        btn = QPushButton(text)
        btn.setObjectName("modernNavButton")
        btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        btn.setMinimumHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self.show_page(page_index))
        return btn

    def show_page(self, index: int):
        """Navigate to page"""
        page_name = self.page_names.get(index, f"UNKNOWN_{index}")
        logger.info(f"Navigation → {page_name}")

        self.content_stack.setCurrentIndex(index)

        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def handle_logout(self):
        """Logout"""
        logger.warning("Logout requested")

        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if hasattr(self.home_page, 'cleanup'):
                self.home_page.cleanup()

            self.auth_service.logout()
            logger.info("User logged out")

            self.close()

            from ui.login_window import LoginWindow
            self.login_window = LoginWindow(self.auth_service)
            self.login_window.show()

    def apply_modern_styles(self):
        """Modern web-style design"""
        base = self.apply_base_stylesheet()

        styles = """
            /* Modern Sidebar - Clean white background */
            #modernSidebar {
                background-color: #FFFFFF;
                border-right: 1px solid #E5E7EB;
            }
            
            /* User card */
            #userCard {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
            }
            
            /* Modern nav buttons - Clean & minimal */
            #modernNavButton {
                background-color: transparent;
                color: #6B7280;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 12px;
                font-size: 13px;
            }
            
            #modernNavButton:hover {
                background-color: #F3F4F6;
                color: #111827;
            }
            
            #modernNavButton:checked {
                background-color: #EFF6FF;
                color: #2563EB;
                font-weight: 600;
                border-left: 3px solid #2563EB;
            }
            
            /* Modern logout button */
            #modernLogoutButton {
                background-color: #FEE2E2;
                color: #DC2626;
                border: 1px solid #FCA5A5;
                border-radius: 8px;
                font-size: 12px;
            }
            
            #modernLogoutButton:hover {
                background-color: #FECACA;
                border-color: #F87171;
            }
            
            /* Content area */
            #contentStack {
                background-color: #F9FAFB;
            }
            
            #homePage, #contentPage {
                background-color: #F9FAFB;
            }
            
            /* Stat cards */
            #statCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E5E7EB;
            }
            
            /* Action card */
            #mainActionCard {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E5E7EB;
                min-height: 240px;
            }
            
            /* Start button */
            #startButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10B981, stop:1 #059669);
                color: #FFFFFF;
                border: none;
                border-radius: 12px;
            }
            
            #startButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #047857);
            }
            
                /* Package cards */
            #packageCard {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
            }
            
            #packageCard:hover {
                border-color: #3B82F6;
            }
            
            /* Purchase button */
            #purchaseButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3B82F6, stop:1 #2563EB);
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
            }
            
            #purchaseButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563EB, stop:1 #1D4ED8);
            }
        """

        self.setStyleSheet(base + styles)