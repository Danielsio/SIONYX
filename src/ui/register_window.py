"""
Registration Window - Inherits from BaseKioskWindow
"""

from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QFrame,
                              QApplication, QGraphicsDropShadowEffect, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from ui.base_window import BaseKioskWindow
from ui.styles import REGISTER_WINDOW_QSS
from utils.const import APP_NAME


class RegisterWindow(BaseKioskWindow):
    """Registration window - inherits kiosk functionality"""

    registration_success = pyqtSignal()
    back_to_login = pyqtSignal()

    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle(f"{APP_NAME} - Create Account")
        self.setObjectName("RegisterWindow")

        # Use base class method
        main_layout = self.create_main_layout()

        # Center container
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(30)

        # Title
        title_label = QLabel("Create Account")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 40, QFont.Weight.Bold))
        title_label.setObjectName("registerTitle")

        subtitle_label = QLabel(f"Join {APP_NAME} Today")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setFont(QFont("Segoe UI", 14))
        subtitle_label.setObjectName("registerSubtitle")

        # Card
        self.card_frame = QFrame()
        self.card_frame.setObjectName("registerCard")
        self.card_frame.setFixedSize(540, 720)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.card_frame.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(50, 40, 50, 40)

        # First Name
        first_name_label = QLabel("First Name *")
        first_name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        first_name_label.setObjectName("fieldLabel")

        self.first_name_input = QLineEdit()
        self.first_name_input.setObjectName("inputField")
        self.first_name_input.setPlaceholderText("Enter your first name")
        self.first_name_input.setFont(QFont("Segoe UI", 13))
        self.first_name_input.setFixedHeight(52)

        # Last Name
        last_name_label = QLabel("Last Name *")
        last_name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        last_name_label.setObjectName("fieldLabel")

        self.last_name_input = QLineEdit()
        self.last_name_input.setObjectName("inputField")
        self.last_name_input.setPlaceholderText("Enter your last name")
        self.last_name_input.setFont(QFont("Segoe UI", 13))
        self.last_name_input.setFixedHeight(52)

        # Phone
        phone_label = QLabel("Phone Number *")
        phone_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        phone_label.setObjectName("fieldLabel")

        self.phone_input = QLineEdit()
        self.phone_input.setObjectName("inputField")
        self.phone_input.setPlaceholderText("+1 234 567 8900")
        self.phone_input.setFont(QFont("Segoe UI", 13))
        self.phone_input.setFixedHeight(52)

        # Email
        email_label = QLabel("Email (Optional)")
        email_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        email_label.setObjectName("fieldLabel")

        self.email_input = QLineEdit()
        self.email_input.setObjectName("inputField")
        self.email_input.setPlaceholderText("your.email@example.com")
        self.email_input.setFont(QFont("Segoe UI", 13))
        self.email_input.setFixedHeight(52)

        # Password
        password_label = QLabel("Password *")
        password_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        password_label.setObjectName("fieldLabel")

        self.password_input = QLineEdit()
        self.password_input.setObjectName("inputField")
        self.password_input.setPlaceholderText("Minimum 6 characters")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Segoe UI", 13))
        self.password_input.setFixedHeight(52)

        # Confirm Password
        confirm_label = QLabel("Confirm Password *")
        confirm_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        confirm_label.setObjectName("fieldLabel")

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setObjectName("inputField")
        self.confirm_password_input.setPlaceholderText("Re-enter your password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setFont(QFont("Segoe UI", 13))
        self.confirm_password_input.setFixedHeight(52)

        # Register button
        self.register_button = QPushButton("Create Account")
        self.register_button.setObjectName("primaryButton")
        self.register_button.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.register_button.setFixedHeight(56)
        self.register_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_button.clicked.connect(self.handle_register)

        # Back to login
        login_container = QWidget()
        login_layout = QHBoxLayout(login_container)
        login_layout.setSpacing(8)

        login_text = QLabel("Already have an account?")
        login_text.setFont(QFont("Segoe UI", 11))
        login_text.setObjectName("mutedText")

        self.login_link = QLabel("<a href='#' style='color: #1976D2; text-decoration: none; font-weight: 600;'>Sign In</a>")
        self.login_link.setFont(QFont("Segoe UI", 11))
        self.login_link.linkActivated.connect(self.go_back_to_login)

        login_layout.addStretch()
        login_layout.addWidget(login_text)
        login_layout.addWidget(self.login_link)
        login_layout.addStretch()

        # Add to card
        card_layout.addWidget(first_name_label)
        card_layout.addWidget(self.first_name_input)
        card_layout.addWidget(last_name_label)
        card_layout.addWidget(self.last_name_input)
        card_layout.addWidget(phone_label)
        card_layout.addWidget(self.phone_input)
        card_layout.addWidget(email_label)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(password_label)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(confirm_label)
        card_layout.addWidget(self.confirm_password_input)
        card_layout.addSpacing(12)
        card_layout.addWidget(self.register_button)
        card_layout.addSpacing(10)
        card_layout.addWidget(login_container)

        # Add to center
        center_layout.addWidget(title_label)
        center_layout.addWidget(subtitle_label)
        center_layout.addWidget(self.card_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(center_widget)
        self.setLayout(main_layout)

        # Apply base + register styles
        self.setStyleSheet(self.apply_base_stylesheet() + REGISTER_WINDOW_QSS)

        self.confirm_password_input.returnPressed.connect(self.handle_register)
        QTimer.singleShot(100, lambda: self.first_name_input.setFocus())

    def handle_register(self):
        """Handle registration"""
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not first_name:
            self.show_error("Validation Error", "Please enter your first name")
            self.first_name_input.setFocus()
            self.shake_widget(self.first_name_input)
            return

        if not last_name:
            self.show_error("Validation Error", "Please enter your last name")
            self.last_name_input.setFocus()
            self.shake_widget(self.last_name_input)
            return

        if not phone:
            self.show_error("Validation Error", "Please enter your phone number")
            self.phone_input.setFocus()
            self.shake_widget(self.phone_input)
            return

        if not password:
            self.show_error("Validation Error", "Please enter a password")
            self.password_input.setFocus()
            self.shake_widget(self.password_input)
            return

        if len(password) < 6:
            self.show_error("Validation Error", "Password must be at least 6 characters")
            self.password_input.setFocus()
            self.shake_widget(self.password_input)
            return

        if password != confirm_password:
            self.show_error("Validation Error", "Passwords do not match")
            self.confirm_password_input.clear()
            self.confirm_password_input.setFocus()
            self.shake_widget(self.confirm_password_input)
            return

        self.register_button.setEnabled(False)
        self.register_button.setText("Creating Account...")
        QApplication.processEvents()

        result = self.auth_service.register(
            phone=phone,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        self.register_button.setEnabled(True)
        self.register_button.setText("Create Account")

        if result['success']:
            self.show_success("Registration Successful", f"Welcome to {APP_NAME}!")
            self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
            self.registration_success.emit()
        else:
            self.show_error("Registration Failed", result.get('error', 'Could not create account'))
            self.shake_widget(self.card_frame)

    def go_back_to_login(self):
        """Go back to login"""
        self.back_to_login.emit()