"""
Login Window - Inherits from BaseKioskWindow
"""

from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QMessageBox,
                             QApplication, QGraphicsDropShadowEffect, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from ui.base_window import BaseKioskWindow
from ui.styles import LOGIN_WINDOW_QSS
from utils.const import APP_NAME


class LoginWindow(BaseKioskWindow):
    """Login window - inherits kiosk functionality"""

    login_success = pyqtSignal()

    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self.init_ui()

    def init_ui(self):
        """Initialize UI - no duplicate setup code"""
        self.setWindowTitle(f"{APP_NAME} - Login")

        # Use base class method for layout
        main_layout = self.create_main_layout()

        # Center container
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(35)

        # Logo Section
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setSpacing(12)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(APP_NAME)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #1976D2; letter-spacing: 4px;")

        subtitle_label = QLabel("Premium PC Time Management")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setFont(QFont("Segoe UI", 15))
        subtitle_label.setStyleSheet("color: #546E7A;")

        logo_layout.addWidget(title_label)
        logo_layout.addWidget(subtitle_label)

        # Login Card
        self.card_frame = QFrame()
        self.card_frame.setObjectName("loginCard")
        self.card_frame.setFixedSize(520, 600)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.card_frame.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(50, 50, 50, 50)

        # Welcome
        welcome_label = QLabel("Welcome Back")
        welcome_label.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        welcome_label.setStyleSheet("color: #212121;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Sign in to access your workstation")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: #616161;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Phone Input
        phone_label = QLabel("Phone Number")
        phone_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        phone_label.setStyleSheet("color: #424242;")

        self.phone_input = QLineEdit()
        self.phone_input.setObjectName("inputField")
        self.phone_input.setPlaceholderText("+1 234 567 8900")
        self.phone_input.setFont(QFont("Segoe UI", 13))
        self.phone_input.setFixedHeight(56)

        # Password Input
        password_label = QLabel("Password")
        password_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        password_label.setStyleSheet("color: #424242;")

        self.password_input = QLineEdit()
        self.password_input.setObjectName("inputField")
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Segoe UI", 13))
        self.password_input.setFixedHeight(56)

        # Forgot password
        forgot_label = QLabel("<a href='#' style='color: #1976D2; text-decoration: none; font-weight: 600;'>Forgot Password?</a>")
        forgot_label.setFont(QFont("Segoe UI", 10))
        forgot_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        forgot_label.linkActivated.connect(self.forgot_password_clicked)

        # Login button
        self.login_button = QPushButton("Sign In")
        self.login_button.setObjectName("primaryButton")
        self.login_button.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.login_button.setFixedHeight(56)
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.clicked.connect(self.handle_login)

        # Register section
        register_container = QWidget()
        register_layout = QHBoxLayout(register_container)
        register_layout.setContentsMargins(0, 0, 0, 0)
        register_layout.setSpacing(8)

        register_text = QLabel("Don't have an account?")
        register_text.setFont(QFont("Segoe UI", 11))
        register_text.setStyleSheet("color: #616161;")

        self.register_link = QLabel("<a href='#' style='color: #1976D2; text-decoration: none; font-weight: 600;'>Sign Up</a>")
        self.register_link.setFont(QFont("Segoe UI", 11))
        self.register_link.linkActivated.connect(self.show_register_window)

        register_layout.addStretch()
        register_layout.addWidget(register_text)
        register_layout.addWidget(self.register_link)
        register_layout.addStretch()

        # Admin exit hint
        exit_hint = QLabel("Admin: Press Ctrl+Alt+Q to exit")
        exit_hint.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        exit_hint.setStyleSheet("""
            color: #E91E63;
            background-color: #FCE4EC;
            padding: 10px 16px;
            border-radius: 12px;
        """)
        exit_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add to card
        card_layout.addWidget(welcome_label)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(10)
        card_layout.addWidget(phone_label)
        card_layout.addWidget(self.phone_input)
        card_layout.addSpacing(5)
        card_layout.addWidget(password_label)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(forgot_label)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.login_button)
        card_layout.addSpacing(15)
        card_layout.addWidget(register_container)
        card_layout.addWidget(exit_hint)

        # Add to center
        center_layout.addWidget(logo_container)
        center_layout.addWidget(self.card_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(center_widget)
        self.setLayout(main_layout)

        # Apply base + login styles
        self.setStyleSheet(self.apply_base_stylesheet() + LOGIN_WINDOW_QSS)

        # Enable Enter key
        self.password_input.returnPressed.connect(self.handle_login)

        # Auto-focus
        QTimer.singleShot(100, lambda: self.phone_input.setFocus())

    def handle_login(self):
        """Handle login"""
        phone = self.phone_input.text().strip()
        password = self.password_input.text()

        if not phone:
            self.show_error("Validation Error", "Please enter your phone number")
            self.phone_input.setFocus()
            self.shake_widget(self.phone_input)
            return

        if not password:
            self.show_error("Validation Error", "Please enter your password")
            self.password_input.setFocus()
            self.shake_widget(self.password_input)
            return

        self.login_button.setEnabled(False)
        self.login_button.setText("Signing In...")
        QApplication.processEvents()

        result = self.auth_service.login(phone, password)

        self.login_button.setEnabled(True)
        self.login_button.setText("Sign In")

        if result['success']:
            self.show_success("Login Successful", "Welcome back!")
            self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
            self.login_success.emit()
        else:
            self.show_error("Login Failed", result.get('error', 'Invalid credentials'))
            self.password_input.clear()
            self.password_input.setFocus()
            self.shake_widget(self.card_frame)

    def show_register_window(self):
        """Show registration window"""
        from ui.register_window import RegisterWindow
        self.register_window = RegisterWindow(self.auth_service)
        self.register_window.registration_success.connect(self.on_registration_success)
        self.register_window.back_to_login.connect(self.on_back_to_login)
        self.register_window.show()
        self.hide()

    def on_registration_success(self):
        """Handle successful registration"""
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        self.login_success.emit()
        if hasattr(self, 'register_window'):
            self.register_window.close()

    def on_back_to_login(self):
        """Handle back to login"""
        self.show()
        if hasattr(self, 'register_window'):
            self.register_window.close()

    def forgot_password_clicked(self):
        """Handle forgot password"""
        self.show_info(
            "Password Reset",
            "Forgot your password?",
            "Please contact your system administrator.<br><br>"
            "<b>Email:</b> support@sionyx.com<br>"
            "<b>Phone:</b> +1 (555) 123-4567"
        )