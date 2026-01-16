"""
Unified Authentication Window - Sign In / Sign Up with sliding panels
Inspired by modern web design with smooth animations
"""

from PyQt6.QtCore import (
    QEasingCurve,
    QObject,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QRect,
    Qt,
    QThread,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.organization_metadata_service import OrganizationMetadataService
from ui.base_window import BaseKioskWindow
from ui.components.loading_overlay import LoadingOverlay
from ui.styles.auth_window import AUTH_WINDOW_QSS
from utils.const import APP_NAME


class AuthWorker(QObject):
    """Worker for running auth operations in background thread"""

    finished = pyqtSignal(dict)

    def __init__(self, operation, *args, **kwargs):
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """Execute the auth operation and emit result"""
        try:
            result = self.operation(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"success": False, "error": str(e)})


class AuthWindow(BaseKioskWindow):
    """Unified authentication window with sliding panels"""

    login_success = pyqtSignal()

    def __init__(self, auth_service):
        super().__init__()
        self.auth_service = auth_service
        self.is_sign_up_mode = False
        self.init_ui()

    def init_ui(self):
        """Initialize UI with sliding panels"""
        self.setWindowTitle(f"{APP_NAME} - אימות")
        self.setObjectName("AuthWindow")

        # Set RTL layout direction for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Use base class method for layout
        main_layout = self.create_main_layout()

        # Center container - fixed size like the web version (768x480)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Main container with fixed size
        self.container = QWidget()
        self.container.setObjectName("authContainer")
        self.container.setFixedSize(900, 600)

        # Add shadow to container
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setXOffset(0)
        shadow.setYOffset(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(shadow)

        # No layout manager - we'll position panels manually with absolute positioning

        # Create the three main components
        self.create_sign_in_panel()
        self.create_sign_up_panel()
        self.create_overlay_panel()

        # Set initial positions
        self.reset_positions()

        center_layout.addWidget(self.container)
        main_layout.addWidget(center_widget)
        self.setLayout(main_layout)

        # Apply styles
        self.setStyleSheet(self.apply_base_stylesheet() + AUTH_WINDOW_QSS)

        # Create loading overlay (attached to the main window, not container)
        self.loading_overlay = LoadingOverlay(self)

        # Focus on sign-in email by default
        QTimer.singleShot(100, lambda: self.signin_email_input.setFocus())

    def create_sign_in_panel(self):
        """Create sign-in form panel"""
        self.signin_panel = QFrame(self.container)
        self.signin_panel.setObjectName("formPanel")
        self.signin_panel.setFixedSize(450, 600)

        layout = QVBoxLayout(self.signin_panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(60, 60, 60, 60)

        # Title
        title = QLabel("התחברות")
        title.setObjectName("formTitle")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Subtitle
        subtitle = QLabel("הזן את פרטי ההתחברות שלך")
        subtitle.setObjectName("formSubtitle")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Phone/Email Input
        self.signin_email_input = QLineEdit()
        self.signin_email_input.setObjectName("authInput")
        self.signin_email_input.setPlaceholderText("מספר טלפון")
        self.signin_email_input.setFont(QFont("Segoe UI", 12))
        self.signin_email_input.setFixedHeight(50)

        # Password Input
        self.signin_password_input = QLineEdit()
        self.signin_password_input.setObjectName("authInput")
        self.signin_password_input.setPlaceholderText("סיסמה")
        self.signin_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.signin_password_input.setFont(QFont("Segoe UI", 12))
        self.signin_password_input.setFixedHeight(50)

        # Forgot password link
        forgot_link = QLabel(
            "<a href='#' style='color: #333; text-decoration: none; font-weight: 600;'>שכחת את הסיסמה?</a>"
        )
        forgot_link.setFont(QFont("Segoe UI", 10))
        forgot_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        forgot_link.linkActivated.connect(self.forgot_password_clicked)

        # Sign In button
        self.signin_button = QPushButton("התחבר")
        self.signin_button.setObjectName("authButton")
        self.signin_button.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.signin_button.setFixedHeight(50)
        self.signin_button.setFixedWidth(180)
        self.signin_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.signin_button.clicked.connect(self.handle_sign_in)

        # Add widgets
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(self.signin_email_input)
        layout.addWidget(self.signin_password_input)
        layout.addWidget(forgot_link)
        layout.addSpacing(10)
        layout.addWidget(self.signin_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        # Enable Enter key
        self.signin_password_input.returnPressed.connect(self.handle_sign_in)

    def create_sign_up_panel(self):
        """Create sign-up form panel"""
        self.signup_panel = QFrame(self.container)
        self.signup_panel.setObjectName("formPanel")
        self.signup_panel.setFixedSize(450, 600)

        layout = QVBoxLayout(self.signup_panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)
        layout.setContentsMargins(60, 40, 60, 40)

        # Title
        title = QLabel("צור חשבון")
        title.setObjectName("formTitle")
        title.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Subtitle
        subtitle = QLabel("מלא את הפרטים שלך כדי להתחיל")
        subtitle.setObjectName("formSubtitle")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # First Name
        self.signup_firstname_input = QLineEdit()
        self.signup_firstname_input.setObjectName("authInput")
        self.signup_firstname_input.setPlaceholderText("שם פרטי")
        self.signup_firstname_input.setFont(QFont("Segoe UI", 12))
        self.signup_firstname_input.setFixedHeight(48)

        # Last Name
        self.signup_lastname_input = QLineEdit()
        self.signup_lastname_input.setObjectName("authInput")
        self.signup_lastname_input.setPlaceholderText("שם משפחה")
        self.signup_lastname_input.setFont(QFont("Segoe UI", 12))
        self.signup_lastname_input.setFixedHeight(48)

        # Phone
        self.signup_phone_input = QLineEdit()
        self.signup_phone_input.setObjectName("authInput")
        self.signup_phone_input.setPlaceholderText("מספר טלפון")
        self.signup_phone_input.setFont(QFont("Segoe UI", 12))
        self.signup_phone_input.setFixedHeight(48)

        # Email (optional)
        self.signup_email_input = QLineEdit()
        self.signup_email_input.setObjectName("authInput")
        self.signup_email_input.setPlaceholderText("אימייל (אופציונלי)")
        self.signup_email_input.setFont(QFont("Segoe UI", 12))
        self.signup_email_input.setFixedHeight(48)

        # Password
        self.signup_password_input = QLineEdit()
        self.signup_password_input.setObjectName("authInput")
        self.signup_password_input.setPlaceholderText("סיסמה")
        self.signup_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_password_input.setFont(QFont("Segoe UI", 12))
        self.signup_password_input.setFixedHeight(48)

        # Confirm Password
        self.signup_confirm_input = QLineEdit()
        self.signup_confirm_input.setObjectName("authInput")
        self.signup_confirm_input.setPlaceholderText("אשר סיסמה")
        self.signup_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_confirm_input.setFont(QFont("Segoe UI", 12))
        self.signup_confirm_input.setFixedHeight(48)

        # Sign Up button
        self.signup_button = QPushButton("הירשם")
        self.signup_button.setObjectName("authButton")
        self.signup_button.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.signup_button.setFixedHeight(50)
        self.signup_button.setFixedWidth(180)
        self.signup_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.signup_button.clicked.connect(self.handle_sign_up)

        # Add widgets
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(self.signup_firstname_input)
        layout.addWidget(self.signup_lastname_input)
        layout.addWidget(self.signup_phone_input)
        layout.addWidget(self.signup_email_input)
        layout.addWidget(self.signup_password_input)
        layout.addWidget(self.signup_confirm_input)
        layout.addSpacing(10)
        layout.addWidget(self.signup_button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        # Enable Enter key
        self.signup_confirm_input.returnPressed.connect(self.handle_sign_up)

    def create_overlay_panel(self):
        """Create the sliding overlay panel with gradients"""
        # Overlay container (holds both overlay panels)
        self.overlay_container = QWidget(self.container)
        self.overlay_container.setObjectName("overlayContainer")
        self.overlay_container.setFixedSize(450, 600)

        # Main overlay with gradient (200% width to slide)
        self.overlay = QWidget(self.overlay_container)
        self.overlay.setObjectName("overlay")
        self.overlay.setFixedSize(900, 600)

        # Left overlay panel (Welcome Back)
        self.overlay_left = QWidget(self.overlay)
        self.overlay_left.setObjectName("overlayPanel")
        self.overlay_left.setFixedSize(450, 600)

        left_layout = QVBoxLayout(self.overlay_left)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.setSpacing(20)
        left_layout.setContentsMargins(50, 50, 50, 50)

        left_title = QLabel("ברוך השב!")
        left_title.setObjectName("overlayTitle")
        left_title.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        left_text = QLabel("כדי להישאר מחובר אלינו\nאנא התחבר עם הפרטים האישיים שלך")
        left_text.setObjectName("overlayText")
        left_text.setFont(QFont("Segoe UI", 13))
        left_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_text.setWordWrap(True)

        self.left_button = QPushButton("התחבר")
        self.left_button.setObjectName("overlayButton")
        self.left_button.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.left_button.setFixedHeight(50)
        self.left_button.setFixedWidth(180)
        self.left_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.left_button.clicked.connect(self.toggle_to_sign_in)

        left_layout.addWidget(left_title)
        left_layout.addWidget(left_text)
        left_layout.addSpacing(20)
        left_layout.addWidget(self.left_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Right overlay panel (Hello Friend)
        self.overlay_right = QWidget(self.overlay)
        self.overlay_right.setObjectName("overlayPanel")
        self.overlay_right.setFixedSize(450, 600)

        right_layout = QVBoxLayout(self.overlay_right)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.setSpacing(20)
        right_layout.setContentsMargins(50, 50, 50, 50)

        right_title = QLabel("שלום, חבר!")
        right_title.setObjectName("overlayTitle")
        right_title.setFont(QFont("Segoe UI", 36, QFont.Weight.Bold))
        right_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_text = QLabel("הזן את הפרטים האישיים שלך\nוהתחל את המסע שלך איתנו")
        right_text.setObjectName("overlayText")
        right_text.setFont(QFont("Segoe UI", 13))
        right_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_text.setWordWrap(True)

        self.right_button = QPushButton("הירשם")
        self.right_button.setObjectName("overlayButton")
        self.right_button.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.right_button.setFixedHeight(50)
        self.right_button.setFixedWidth(180)
        self.right_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.right_button.clicked.connect(self.toggle_to_sign_up)

        right_layout.addWidget(right_title)
        right_layout.addWidget(right_text)
        right_layout.addSpacing(20)
        right_layout.addWidget(
            self.right_button, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Position overlay panels
        self.overlay_left.move(0, 0)
        self.overlay_right.move(450, 0)

    def reset_positions(self):
        """Set initial positions for all panels"""
        # Sign-in on the left, sign-up on the left (hidden), overlay on the right
        self.signin_panel.move(0, 0)
        self.signup_panel.move(0, 0)
        self.signup_panel.hide()

        self.overlay_container.move(450, 0)
        self.overlay.move(-450, 0)

        # Ensure overlay is on top (critical for proper layering)
        self.overlay_container.raise_()

    def toggle_to_sign_up(self):
        """Animate transition to sign-up mode"""
        if self.is_sign_up_mode:
            return

        self.is_sign_up_mode = True
        self.signup_panel.show()

        # Ensure proper z-order: forms below, overlay on top
        self.signin_panel.lower()
        self.signup_panel.lower()
        self.overlay_container.raise_()

        # Create animation group
        anim_group = QParallelAnimationGroup(self)

        # Slide sign-in panel to the right
        signin_anim = QPropertyAnimation(self.signin_panel, b"geometry")
        signin_anim.setDuration(600)
        signin_anim.setStartValue(self.signin_panel.geometry())
        signin_anim.setEndValue(QRect(450, 0, 450, 600))
        signin_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Slide sign-up panel to the right
        signup_anim = QPropertyAnimation(self.signup_panel, b"geometry")
        signup_anim.setDuration(600)
        signup_anim.setStartValue(self.signup_panel.geometry())
        signup_anim.setEndValue(QRect(450, 0, 450, 600))
        signup_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Slide overlay container to the left
        overlay_container_anim = QPropertyAnimation(self.overlay_container, b"geometry")
        overlay_container_anim.setDuration(600)
        overlay_container_anim.setStartValue(self.overlay_container.geometry())
        overlay_container_anim.setEndValue(QRect(0, 0, 450, 600))
        overlay_container_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Slide inner overlay to show left panel
        overlay_anim = QPropertyAnimation(self.overlay, b"geometry")
        overlay_anim.setDuration(600)
        overlay_anim.setStartValue(self.overlay.geometry())
        overlay_anim.setEndValue(QRect(0, 0, 900, 600))
        overlay_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        anim_group.addAnimation(signin_anim)
        anim_group.addAnimation(signup_anim)
        anim_group.addAnimation(overlay_container_anim)
        anim_group.addAnimation(overlay_anim)

        anim_group.finished.connect(lambda: self.signin_panel.hide())
        anim_group.start()

        # Focus on first input after animation
        QTimer.singleShot(650, lambda: self.signup_firstname_input.setFocus())

    def toggle_to_sign_in(self):
        """Animate transition to sign-in mode"""
        if not self.is_sign_up_mode:
            return

        self.is_sign_up_mode = False
        self.signin_panel.show()

        # Ensure proper z-order: forms below, overlay on top
        self.signin_panel.lower()
        self.signup_panel.lower()
        self.overlay_container.raise_()

        # Create animation group
        anim_group = QParallelAnimationGroup(self)

        # Slide sign-in panel back to the left
        signin_anim = QPropertyAnimation(self.signin_panel, b"geometry")
        signin_anim.setDuration(600)
        signin_anim.setStartValue(self.signin_panel.geometry())
        signin_anim.setEndValue(QRect(0, 0, 450, 600))
        signin_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Slide sign-up panel back to the left
        signup_anim = QPropertyAnimation(self.signup_panel, b"geometry")
        signup_anim.setDuration(600)
        signup_anim.setStartValue(self.signup_panel.geometry())
        signup_anim.setEndValue(QRect(0, 0, 450, 600))
        signup_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Slide overlay container back to the right
        overlay_container_anim = QPropertyAnimation(self.overlay_container, b"geometry")
        overlay_container_anim.setDuration(600)
        overlay_container_anim.setStartValue(self.overlay_container.geometry())
        overlay_container_anim.setEndValue(QRect(450, 0, 450, 600))
        overlay_container_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # Slide inner overlay back to show right panel
        overlay_anim = QPropertyAnimation(self.overlay, b"geometry")
        overlay_anim.setDuration(600)
        overlay_anim.setStartValue(self.overlay.geometry())
        overlay_anim.setEndValue(QRect(-450, 0, 900, 600))
        overlay_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        anim_group.addAnimation(signin_anim)
        anim_group.addAnimation(signup_anim)
        anim_group.addAnimation(overlay_container_anim)
        anim_group.addAnimation(overlay_anim)

        anim_group.finished.connect(lambda: self.signup_panel.hide())
        anim_group.start()

        # Focus on first input after animation
        QTimer.singleShot(650, lambda: self.signin_email_input.setFocus())

    def handle_sign_in(self):
        """Handle sign-in"""
        phone = self.signin_email_input.text().strip()
        password = self.signin_password_input.text()

        if not phone:
            self.show_error("שגיאת אימות", "אנא הזן את מספר הטלפון שלך")
            self.signin_email_input.setFocus()
            self.shake_widget(self.signin_email_input)
            return

        if not password:
            self.show_error("שגיאת אימות", "אנא הזן את הסיסמה שלך")
            self.signin_password_input.setFocus()
            self.shake_widget(self.signin_password_input)
            return

        # Show loading overlay and disable button
        self.loading_overlay.show_with_message("מתחבר...")
        self.signin_button.setEnabled(False)

        # Create worker and thread for async operation
        self._login_thread = QThread()
        self._login_worker = AuthWorker(self.auth_service.login, phone, password)
        self._login_worker.moveToThread(self._login_thread)

        # Connect signals
        self._login_thread.started.connect(self._login_worker.run)
        self._login_worker.finished.connect(self._on_login_complete)
        self._login_worker.finished.connect(self._login_thread.quit)
        self._login_worker.finished.connect(self._login_worker.deleteLater)
        self._login_thread.finished.connect(self._login_thread.deleteLater)

        # Start the thread
        self._login_thread.start()

    def _on_login_complete(self, result):
        """Handle login completion (called from main thread)"""
        # Hide loading overlay and re-enable button
        self.loading_overlay.hide_overlay()
        self.signin_button.setEnabled(True)

        if result["success"]:
            self.show_success("התחברות הצליחה", "ברוך השב!")
            self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
            self.login_success.emit()
        else:
            self.show_error(
                "התחברות נכשלה", result.get("error", "פרטי התחברות לא תקינים")
            )
            self.signin_password_input.clear()
            self.signin_password_input.setFocus()
            self.shake_widget(self.signin_panel)

    def handle_sign_up(self):
        """Handle sign-up"""
        first_name = self.signup_firstname_input.text().strip()
        last_name = self.signup_lastname_input.text().strip()
        phone = self.signup_phone_input.text().strip()
        email = self.signup_email_input.text().strip()
        password = self.signup_password_input.text()
        confirm_password = self.signup_confirm_input.text()

        if not first_name:
            self.show_error("שגיאת אימות", "אנא הזן את השם הפרטי שלך")
            self.signup_firstname_input.setFocus()
            self.shake_widget(self.signup_firstname_input)
            return

        if not last_name:
            self.show_error("שגיאת אימות", "אנא הזן את שם המשפחה שלך")
            self.signup_lastname_input.setFocus()
            self.shake_widget(self.signup_lastname_input)
            return

        if not phone:
            self.show_error("שגיאת אימות", "אנא הזן את מספר הטלפון שלך")
            self.signup_phone_input.setFocus()
            self.shake_widget(self.signup_phone_input)
            return

        if not password:
            self.show_error("שגיאת אימות", "אנא הזן סיסמה")
            self.signup_password_input.setFocus()
            self.shake_widget(self.signup_password_input)
            return

        if len(password) < 6:
            self.show_error("שגיאת אימות", "הסיסמה חייבת להכיל לפחות 6 תווים")
            self.signup_password_input.setFocus()
            self.shake_widget(self.signup_password_input)
            return

        if password != confirm_password:
            self.show_error("שגיאת אימות", "הסיסמאות אינן תואמות")
            self.signup_confirm_input.clear()
            self.signup_confirm_input.setFocus()
            self.shake_widget(self.signup_confirm_input)
            return

        # Show loading overlay and disable button
        self.loading_overlay.show_with_message("יוצר חשבון...")
        self.signup_button.setEnabled(False)

        # Create worker and thread for async operation
        self._register_thread = QThread()
        self._register_worker = AuthWorker(
            self.auth_service.register,
            phone=phone,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        self._register_worker.moveToThread(self._register_thread)

        # Connect signals
        self._register_thread.started.connect(self._register_worker.run)
        self._register_worker.finished.connect(self._on_register_complete)
        self._register_worker.finished.connect(self._register_thread.quit)
        self._register_worker.finished.connect(self._register_worker.deleteLater)
        self._register_thread.finished.connect(self._register_thread.deleteLater)

        # Start the thread
        self._register_thread.start()

    def _on_register_complete(self, result):
        """Handle registration completion (called from main thread)"""
        # Hide loading overlay and re-enable button
        self.loading_overlay.hide_overlay()
        self.signup_button.setEnabled(True)

        if result["success"]:
            self.show_success("ההרשמה הצליחה", f"ברוך הבא ל-{APP_NAME}!")
            self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
            self.login_success.emit()
        else:
            self.show_error("ההרשמה נכשלה", result.get("error", "לא ניתן ליצור חשבון"))
            self.shake_widget(self.signup_panel)

    def forgot_password_clicked(self):
        """Handle forgot password - show admin contact info"""
        try:
            # Try to get admin contact from organization metadata
            org_metadata_service = OrganizationMetadataService(
                self.auth_service.firebase
            )
            org_id = self.auth_service.firebase.org_id

            contact_result = org_metadata_service.get_admin_contact(org_id)

            if contact_result.get("success"):
                contact = contact_result["contact"]
                admin_phone = contact.get("phone", "")
                admin_email = contact.get("email", "")
                org_name = contact.get("org_name", "")

                # Build contact info message in Hebrew
                contact_info = ""
                if admin_phone:
                    contact_info += f"<b>טלפון:</b> {admin_phone}<br>"
                if admin_email:
                    contact_info += f"<b>אימייל:</b> {admin_email}<br>"

                org_display = f" ({org_name})" if org_name else ""

                self.show_info(
                    "איפוס סיסמה",
                    "שכחת את הסיסמה?",
                    f"לאיפוס סיסמה, אנא פנה למנהל הארגון{org_display}.<br><br>"
                    f"{contact_info}<br>"
                    "המנהל יוכל לאפס את הסיסמה שלך דרך לוח הבקרה.",
                )
            else:
                # Fallback if admin contact not found
                self.show_info(
                    "איפוס סיסמה",
                    "שכחת את הסיסמה?",
                    "לאיפוס סיסמה, אנא פנה למנהל הארגון שלך.<br><br>"
                    "המנהל יוכל לאפס את הסיסמה שלך דרך לוח הבקרה.",
                )
        except Exception:
            # Fallback on error
            self.show_info(
                "איפוס סיסמה",
                "שכחת את הסיסמה?",
                "לאיפוס סיסמה, אנא פנה למנהל הארגון שלך.<br><br>"
                "המנהל יוכל לאפס את הסיסמה שלך דרך לוח הבקרה.",
            )
