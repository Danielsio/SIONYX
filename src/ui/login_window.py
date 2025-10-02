"""
Login Window - Full Screen Kiosk Mode
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QPushButton, QFrame, QMessageBox, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QKeySequence, QShortcut


class LoginWindow(QWidget):
    """Login window with modern design and kiosk mode"""

    login_success = pyqtSignal()

    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self.init_ui()
        self.setup_kiosk_mode()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Sionyx - Login")

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
        main_layout.setSpacing(0)

        # Center container
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(25)

        # Logo/Title Section
        title_label = QLabel("SIONYX")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 42, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2196F3; margin-bottom: 5px;")

        # Updated tagline options (choose one):
        tagline_options = [
            "Premium PC Time Management",
            "Secure Workstation Access",
            "Professional PC Rental Solutions",
            "Smart Time & Print Control",
            "Cloud-Connected PC Management"
        ]

        subtitle_label = QLabel(tagline_options[0])  # Change index to try different ones
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setStyleSheet("color: #666; margin-bottom: 40px;")

        # Login Card - Fixed width
        card_frame = QFrame()
        card_frame.setObjectName("loginCard")
        card_frame.setFixedWidth(480)
        card_layout = QVBoxLayout(card_frame)
        card_layout.setSpacing(18)
        card_layout.setContentsMargins(40, 40, 40, 40)

        # Welcome text
        welcome_label = QLabel("Welcome Back")
        welcome_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        welcome_label.setStyleSheet("color: #333;")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Sign in to access your workstation")
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setStyleSheet("color: #999; margin-bottom: 25px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Phone input - FIXED HEIGHT
        phone_label = QLabel("Phone Number")
        phone_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        phone_label.setStyleSheet("color: #555;")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+1 234 567 8900")
        self.phone_input.setFont(QFont("Arial", 13))
        self.phone_input.setFixedHeight(50)  # FIXED: Explicit height

        # Password input - FIXED HEIGHT
        password_label = QLabel("Password")
        password_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        password_label.setStyleSheet("color: #555;")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Arial", 13))
        self.password_input.setFixedHeight(50)  # FIXED: Explicit height

        # Forgot password
        forgot_layout = QHBoxLayout()
        forgot_label = QLabel("<a href='#' style='color: #2196F3; text-decoration: none;'>Forgot Password?</a>")
        forgot_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        forgot_label.linkActivated.connect(self.forgot_password_clicked)
        forgot_layout.addStretch()
        forgot_layout.addWidget(forgot_label)

        # Login button
        self.login_button = QPushButton("Sign In")
        self.login_button.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.login_button.setFixedHeight(55)
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.clicked.connect(self.handle_login)

        # Register link
        register_layout = QHBoxLayout()
        register_label = QLabel("Don't have an account?")
        register_label.setFont(QFont("Arial", 11))
        register_label.setStyleSheet("color: #666;")

        self.register_link = QLabel("<a href='#' style='color: #2196F3; text-decoration: none; font-weight: bold;'>Sign Up</a>")
        self.register_link.setFont(QFont("Arial", 11))
        self.register_link.linkActivated.connect(self.show_register_window)

        register_layout.addStretch()
        register_layout.addWidget(register_label)
        register_layout.addWidget(self.register_link)
        register_layout.addStretch()

        # Exit hint (small text at bottom)
        exit_hint = QLabel("Press Ctrl+Alt+Q to exit (Admin only)")
        exit_hint.setFont(QFont("Arial", 8))
        exit_hint.setStyleSheet("color: #999; margin-top: 10px;")
        exit_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add widgets to card
        card_layout.addWidget(welcome_label)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(5)
        card_layout.addWidget(phone_label)
        card_layout.addWidget(self.phone_input)
        card_layout.addSpacing(8)
        card_layout.addWidget(password_label)
        card_layout.addWidget(self.password_input)
        card_layout.addLayout(forgot_layout)
        card_layout.addSpacing(15)
        card_layout.addWidget(self.login_button)
        card_layout.addSpacing(20)
        card_layout.addLayout(register_layout)
        card_layout.addWidget(exit_hint)

        # Add to center layout
        center_layout.addWidget(title_label)
        center_layout.addWidget(subtitle_label)
        center_layout.addWidget(card_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        # Add center to main
        main_layout.addWidget(center_widget)

        self.setLayout(main_layout)

        # Apply stylesheet
        self.apply_styles()

        # Enable Enter key to submit
        self.password_input.returnPressed.connect(self.handle_login)

        # Focus on phone input
        QTimer.singleShot(100, lambda: self.phone_input.setFocus())

    def setup_kiosk_mode(self):
        """Setup kiosk mode restrictions"""
        # Disable Alt+F4, Alt+Tab, Windows key (on Windows)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Add admin exit shortcut (Ctrl+Alt+Q)
        self.exit_shortcut = QShortcut(QKeySequence("Ctrl+Alt+Q"), self)
        self.exit_shortcut.activated.connect(self.admin_exit)

        # Prevent minimize/close
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

    def admin_exit(self):
        """Admin exit with password"""
        from PyQt6.QtWidgets import QInputDialog

        password, ok = QInputDialog.getText(
            self,
            "Admin Access",
            "Enter admin password to exit:",
            QLineEdit.EchoMode.Password
        )

        if ok and password == "moshe0040":
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
            
            #loginCard {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #e0e0e0;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            }
            
            QLineEdit {
                padding: 14px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                background-color: #fafafa;
                color: #333;
                font-size: 13px;
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
                font-size: 13px;
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
        """Prevent Escape key from closing"""
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Prevent closing the window"""
        event.ignore()

    def handle_login(self):
        """Handle login button click"""
        phone = self.phone_input.text().strip()
        password = self.password_input.text()

        if not phone:
            self.show_error("Please enter your phone number")
            self.phone_input.setFocus()
            return

        if not password:
            self.show_error("Please enter your password")
            self.password_input.setFocus()
            return

        self.login_button.setEnabled(False)
        self.login_button.setText("Signing In...")

        result = self.auth_service.login(phone, password)

        self.login_button.setEnabled(True)
        self.login_button.setText("Sign In")

        if result['success']:
            self.show_success("Login successful!")
            # Allow closing now
            self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
            self.login_success.emit()
        else:
            self.show_error(result.get('error', 'Login failed'))
            self.password_input.clear()
            self.password_input.setFocus()

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
        """Handle back to login from register"""
        self.show()
        if hasattr(self, 'register_window'):
            self.register_window.close()

    def forgot_password_clicked(self):
        """Handle forgot password click"""
        QMessageBox.information(
            self,
            "Forgot Password",
            "Please contact your administrator to reset your password.\n\n"
            "Support: support@sionyx.com"
        )

    def show_error(self, message: str):
        """Show error message"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Login Error")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def show_success(self, message: str):
        """Show success message"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Success")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()