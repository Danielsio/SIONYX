"""
Registration Window - Full Screen Kiosk Mode
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QFrame, QMessageBox,
                              QScrollArea, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut


class RegisterWindow(QWidget):
    """Registration window with modern design and kiosk mode"""

    registration_success = pyqtSignal()
    back_to_login = pyqtSignal()

    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self.init_ui()
        self.setup_kiosk_mode()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Sionyx - Create Account")

        # Set window flags for kiosk mode
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        # Make fullscreen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.showFullScreen()

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Center container
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(25)

        # Title
        title_label = QLabel("Create Account")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2196F3;")

        subtitle_label = QLabel("Join Sionyx today")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setFont(QFont("Arial", 13))
        subtitle_label.setStyleSheet("color: #666; margin-bottom: 30px;")

        # Registration Card - Fixed width
        card_frame = QFrame()
        card_frame.setObjectName("registerCard")
        card_frame.setFixedWidth(500)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(40, 35, 40, 35)

        # First Name
        first_name_label = QLabel("First Name *")
        first_name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        first_name_label.setStyleSheet("color: #555;")

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Enter your first name")
        self.first_name_input.setFont(QFont("Arial", 12))
        self.first_name_input.setFixedHeight(48)

        # Last Name
        last_name_label = QLabel("Last Name *")
        last_name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        last_name_label.setStyleSheet("color: #555;")

        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Enter your last name")
        self.last_name_input.setFont(QFont("Arial", 12))
        self.last_name_input.setFixedHeight(48)

        # Phone Number
        phone_label = QLabel("Phone Number *")
        phone_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        phone_label.setStyleSheet("color: #555;")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+1 234 567 8900")
        self.phone_input.setFont(QFont("Arial", 12))
        self.phone_input.setFixedHeight(48)

        # Email (Optional)
        email_label = QLabel("Email (Optional)")
        email_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        email_label.setStyleSheet("color: #555;")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your.email@example.com")
        self.email_input.setFont(QFont("Arial", 12))
        self.email_input.setFixedHeight(48)

        # Password
        password_label = QLabel("Password *")
        password_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        password_label.setStyleSheet("color: #555;")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Minimum 6 characters")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Arial", 12))
        self.password_input.setFixedHeight(48)

        # Confirm Password
        confirm_label = QLabel("Confirm Password *")
        confirm_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        confirm_label.setStyleSheet("color: #555;")

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Re-enter your password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setFont(QFont("Arial", 12))
        self.confirm_password_input.setFixedHeight(48)

        # Register button
        self.register_button = QPushButton("Create Account")
        self.register_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.register_button.setFixedHeight(52)
        self.register_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_button.clicked.connect(self.handle_register)

        # Back to login link
        login_layout = QHBoxLayout()
        login_label = QLabel("Already have an account?")
        login_label.setFont(QFont("Arial", 10))
        login_label.setStyleSheet("color: #666;")

        self.login_link = QLabel("<a href='#' style='color: #2196F3; text-decoration: none; font-weight: bold;'>Sign In</a>")
        self.login_link.setFont(QFont("Arial", 10))
        self.login_link.linkActivated.connect(self.go_back_to_login)

        login_layout.addStretch()
        login_layout.addWidget(login_label)
        login_layout.addWidget(self.login_link)
        login_layout.addStretch()

        # Add widgets to card
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
        card_layout.addSpacing(10)
        card_layout.addWidget(self.register_button)
        card_layout.addSpacing(15)
        card_layout.addLayout(login_layout)

        # Add to center layout
        center_layout.addWidget(title_label)
        center_layout.addWidget(subtitle_label)
        center_layout.addWidget(card_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add center to main
        main_layout.addWidget(center_widget)

        self.setLayout(main_layout)

        # Apply stylesheet
        self.apply_styles()

        # Enable Enter key
        self.confirm_password_input.returnPressed.connect(self.handle_register)

        # Focus on first input
        QTimer.singleShot(100, lambda: self.first_name_input.setFocus())

    def setup_kiosk_mode(self):
        """Setup kiosk mode restrictions"""
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Admin exit shortcut
        self.exit_shortcut = QShortcut(QKeySequence("Ctrl+Alt+Q"), self)
        self.exit_shortcut.activated.connect(self.admin_exit)

        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

    def admin_exit(self):
        """Admin exit with password"""
        from PyQt6.QtWidgets import QInputDialog

        password, ok = QInputDialog.getText(
            self,
            "Admin Access",
            "Enter admin password to exit:",
            QLineEdit.EchoMode.Password
        )

        if ok and password == "admin123":
            QApplication.quit()
        elif ok:
            QMessageBox.warning(self, "Access Denied", "Incorrect admin password")

    def apply_styles(self):
        """Apply modern stylesheet"""
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f5f7fa, stop:1 #c3cfe2
                );
            }
            
            #registerCard {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #e0e0e0;
            }
            
            QLineEdit {
                padding: 12px 14px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                background-color: #fafafa;
                color: #333;
            }
            
            QLineEdit:focus {
                border: 2px solid #2196F3;
                background-color: white;
            }
            
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #1976D2;
            }
            
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            
            QPushButton:disabled {
                background-color: #BDBDBD;
            }
        """)

    def keyPressEvent(self, event):
        """Prevent Escape key"""
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Prevent closing"""
        event.ignore()

    def handle_register(self):
        """Handle registration"""
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not first_name:
            self.show_error("Please enter your first name")
            self.first_name_input.setFocus()
            return

        if not last_name:
            self.show_error("Please enter your last name")
            self.last_name_input.setFocus()
            return

        if not phone:
            self.show_error("Please enter your phone number")
            self.phone_input.setFocus()
            return

        if not password:
            self.show_error("Please enter a password")
            self.password_input.setFocus()
            return

        if password != confirm_password:
            self.show_error("Passwords do not match")
            self.confirm_password_input.clear()
            self.confirm_password_input.setFocus()
            return

        if len(password) < 6:
            self.show_error("Password must be at least 6 characters")
            return

        self.register_button.setEnabled(False)
        self.register_button.setText("Creating Account...")

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
            self.show_success("Account created successfully!")
            self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
            self.registration_success.emit()
        else:
            self.show_error(result.get('error', 'Registration failed'))

    def go_back_to_login(self):
        """Go back to login"""
        self.back_to_login.emit()

    def show_error(self, message: str):
        """Show error message"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Registration Error")
        msg.setText(message)
        msg.exec()

    def show_success(self, message: str):
        """Show success message"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Success")
        msg.setText(message)
        msg.exec()