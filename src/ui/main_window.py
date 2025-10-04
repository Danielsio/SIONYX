"""
Main Window - Modern Web-Style Navigation
"""
from typing import Dict

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QStackedWidget, QMessageBox,
                              QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from ui.base_window import BaseKioskWindow
from ui.pages.home_page import HomePage
from ui.pages.packages_page import PackagesPage
from ui.pages.history_page import HistoryPage
from ui.pages.help_page import HelpPage
from utils.logger import get_logger
from ui.floating_timer import FloatingTimer
from services.session_service import SessionService
from ui.styles import MAIN_WINDOW_QSS
from utils.const import APP_NAME

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

        # Session management
        self.session_service = SessionService(
            auth_service.firebase,
            self.current_user['uid']
        )
        self.floating_timer = None

        # Connect session signals
        self.session_service.time_updated.connect(self.on_time_updated)
        self.session_service.session_ended.connect(self.on_session_ended)
        self.session_service.warning_5min.connect(self.on_warning_5min)
        self.session_service.warning_1min.connect(self.on_warning_1min)
        self.session_service.sync_failed.connect(self.on_sync_failed)
        self.session_service.sync_restored.connect(self.on_sync_restored)

        logger.info(f"Dashboard opened: {self.current_user.get('firstName')}")
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle(f"{APP_NAME} - Dashboard")

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
        """Create modern, clean sidebar like the reference UI"""
        sidebar = QFrame()
        sidebar.setObjectName("modernSidebar")
        sidebar.setFixedWidth(240)

        # Subtle elevation like the mock
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 30))
        sidebar.setGraphicsEffect(shadow)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar (burger + brand)
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 18, 20, 14)
        header_layout.setSpacing(10)

        burger = QLabel("≡")
        burger.setFont(QFont("Segoe UI", 18, QFont.Weight.Black))
        burger.setStyleSheet("color: #111827;")

        brand = QLabel(APP_NAME)
        brand.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        brand.setStyleSheet("color: #111827;")

        header_layout.addWidget(burger)
        header_layout.addWidget(brand)
        header_layout.addStretch()

        # Navigation section (no 'MENU' label to match mock)
        nav_section = QWidget()
        nav_layout = QVBoxLayout(nav_section)
        nav_layout.setContentsMargins(12, 6, 12, 10)
        nav_layout.setSpacing(6)

        self.nav_buttons = []

        nav_items = [
            ("🏠  Home", self.PAGES['HOME']),
            ("🧩  Packages", self.PAGES['PACKAGES']),
            ("🕘  History", self.PAGES['HISTORY']),
            ("❓  Help", self.PAGES['HELP'])
        ]

        for label, index in nav_items:
            btn = self.create_modern_nav_button(label, index)
            self.nav_buttons.append(btn)
            nav_layout.addWidget(btn)

        nav_layout.addStretch()

        # Bottom section - Logout
        bottom_section = QWidget()
        bottom_layout = QVBoxLayout(bottom_section)
        bottom_layout.setContentsMargins(12, 6, 12, 20)
        bottom_layout.setSpacing(0)

        btn_logout = QPushButton("Logout")
        btn_logout.setObjectName("modernLogoutButton")
        btn_logout.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        btn_logout.setMinimumHeight(40)
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.clicked.connect(self.handle_logout)
        bottom_layout.addWidget(btn_logout)

        # Compose sidebar
        layout.addWidget(header)
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
        self.setStyleSheet(base + MAIN_WINDOW_QSS)

    def start_user_session(self, remaining_time: int):
        """Start user session and show floating timer"""
        logger.info("Starting user session")

        result = self.session_service.start_session(remaining_time)

        if not result['success']:
            QMessageBox.critical(
                self,
                "Session Error",
                f"Failed to start session: {result['error']}"
            )
            return

        # Create and show floating timer
        self.floating_timer = FloatingTimer()
        self.floating_timer.return_clicked.connect(self.return_from_session)
        self.floating_timer.show()

        # Minimize main window
        self.showMinimized()

        logger.info("Session started, main window minimized")

    def return_from_session(self):
        """User clicked return button on floating timer"""
        logger.info("User returning from session")

        # End session
        result = self.session_service.end_session('user')

        # Close floating timer
        if self.floating_timer:
            self.floating_timer.close()
            self.floating_timer = None

        # Restore main window and go directly to home page
        self.showNormal()
        self.activateWindow()

        # Refresh user data and home page directly - no summary dialog
        if result.get('success'):
            remaining = result.get('remaining_time', 0)
            if hasattr(self.home_page, 'current_user'):
                self.home_page.current_user['remainingTime'] = remaining
            if hasattr(self.home_page, 'update_countdown'):
                self.home_page.update_countdown()
        
        # Switch to home page
        self.content_stack.setCurrentWidget(self.home_page)
        
        logger.info("Returned to home page without summary dialog")

    def on_time_updated(self, remaining_seconds: int):
        """Update floating timer display"""
        if self.floating_timer:
            self.floating_timer.update_time(remaining_seconds)

    def on_session_ended(self, reason: str):
        """Handle session end"""
        logger.warning(f"Session ended: {reason}")

        # Close timer
        if self.floating_timer:
            self.floating_timer.close()
            self.floating_timer = None

        # Restore window
        self.showNormal()
        self.activateWindow()

        # Show appropriate message
        if reason == 'expired':
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Time Expired")
            msg.setText("Your session time has expired!")
            msg.setInformativeText("Would you like to purchase more time?")
            msg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if msg.exec() == QMessageBox.StandardButton.Yes:
                self.show_page(self.PAGES['PACKAGES'])

    def on_warning_5min(self):
        """5 minute warning"""
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Time Warning")
        msg.setText("5 minutes remaining!")
        msg.setInformativeText("Your session will end soon.")
        msg.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        msg.show()
        QTimer.singleShot(3000, msg.close)

    def on_warning_1min(self):
        """1 minute warning"""
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("URGENT")
        msg.setText("Only 1 minute remaining!")
        msg.setInformativeText("Save your work now!")
        msg.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        msg.show()
        QTimer.singleShot(5000, msg.close)

    def on_sync_failed(self, error: str):
        """Handle sync failure"""
        logger.error(f"Sync failed: {error}")
        if self.floating_timer:
            self.floating_timer.set_offline_mode(True)

    def on_sync_restored(self):
        """Handle sync restoration"""
        logger.info("Sync restored")
        if self.floating_timer:
            self.floating_timer.set_offline_mode(False)

    # Session summary method removed - users go directly back to home page