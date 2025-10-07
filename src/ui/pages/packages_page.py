"""
Packages Page
Browse and purchase time/print packages
"""

from typing import Dict
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QGridLayout, QMessageBox,
                             QGraphicsDropShadowEffect, QScrollArea, QDialog)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from services.package_service import PackageService
from utils.logger import get_logger
from ui.styles import PACKAGES_PAGE_QSS

logger = get_logger(__name__)


class PackagesPage(QWidget):
    """Packages browser and purchase page"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.current_user = auth_service.get_current_user()
        self.package_service = PackageService(auth_service.firebase)

        self.packages = []

        self.init_ui()
        self.load_packages()

    def init_ui(self):
        """Initialize UI"""
        self.setObjectName("contentPage")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(45, 35, 45, 35)
        main_layout.setSpacing(25)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Available Packages")
        title.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827;")

        subtitle = QLabel("Purchase additional time and print credits")
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setStyleSheet("color: #6B7280;")

        header_container = QWidget()
        header_vlayout = QVBoxLayout(header_container)
        header_vlayout.setContentsMargins(0, 0, 0, 0)
        header_vlayout.setSpacing(5)
        header_vlayout.addWidget(title)
        header_vlayout.addWidget(subtitle)

        header_layout.addWidget(header_container)
        header_layout.addStretch()

        # Packages grid container (will be populated after load)
        self.packages_container = QWidget()
        self.packages_layout = QGridLayout(self.packages_container)
        self.packages_layout.setSpacing(20)
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self.packages_container)

        # Loading/empty state label
        self.state_label = QLabel("Loading packages...")
        self.state_label.setFont(QFont("Segoe UI", 14))
        self.state_label.setStyleSheet("color: #9CA3AF;")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.state_label)
        main_layout.addWidget(scroll, 1)

        logger.debug("Packages page initialized")
        # Apply page-specific styles
        self.setStyleSheet(PACKAGES_PAGE_QSS)

    def load_packages(self):
        """Load packages from Firebase"""
        logger.info("Loading packages from database")

        # Simulate async load with QTimer
        QTimer.singleShot(500, self._fetch_packages)

    def _fetch_packages(self):
        """Fetch packages from service"""
        result = self.package_service.get_all_packages()

        if not result.get('success'):
            logger.error(f"Failed to load packages: {result.get('error')}")
            self.state_label.setText("❌ Failed to load packages")
            return

        self.packages = result.get('packages', [])

        if len(self.packages) == 0:
            logger.warning("No packages available")
            self.state_label.setText("📦 No packages available yet")
            return

        logger.info(f"Loaded {len(self.packages)} packages")
        self.state_label.hide()
        self.display_packages()

    def display_packages(self):
        """Display packages in grid with improved spacing for larger cards"""
        # Clear existing
        for i in reversed(range(self.packages_layout.count())):
            self.packages_layout.itemAt(i).widget().setParent(None)

        # Update spacing for much larger cards
        self.packages_layout.setSpacing(40)
        self.packages_layout.setContentsMargins(20, 10, 20, 40)

        # Display in grid (adjust columns for larger 380px cards)
        row, col = 0, 0
        max_columns = 3  # Can still fit 3 cards with new spacing
        
        for package in self.packages:
            card = self.create_package_card(package)
            self.packages_layout.addWidget(card, row, col)

            col += 1
            if col >= max_columns:
                col = 0
                row += 1

    def create_package_card(self, package: Dict) -> QFrame:
        """Create an improved package display card with better visual hierarchy"""
        card = HoverFrame()
        card.setObjectName("packageCard")
        card.setFixedSize(400, 520)  # Larger for readability and touch targets
        
        # Add modern border radius to the main card
        card.setStyleSheet("""
            QFrame#packageCard {
                background-color: white;
                border-radius: 20px;
                border: 1px solid #E5E7EB;
            }
        """)
        
        # Determine package tier for styling
        package_tier = self.get_package_tier(package)
        
        # Enhanced shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 40))
        card.setGraphicsEffect(shadow)

        # Main layout
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header accent bar
        header = QFrame()
        header.setFixedHeight(10)
        header.setStyleSheet(f"""
            background-color: {package_tier['accent_color']};
            border-radius: 20px 20px 0 0;
            border: none;
        """)
        
        # Content container with better spacing
        content = QWidget()
        content.setStyleSheet("background-color: white; border-radius: 0 0 20px 20px;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 24, 30, 30)
        content_layout.setSpacing(20)

        # Popular badge (for recommended packages) - improved design
        if package_tier['is_popular']:
            badge = QLabel("🔥 MOST POPULAR")
            badge.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            badge.setStyleSheet(f"""
                color: white;
                background-color: {package_tier['accent_color']};
                padding: 8px 16px;
                border-radius: 16px;
                margin-bottom: 10px;
            """)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setMaximumHeight(32)
            content_layout.addWidget(badge)

        # Package name with better typography
        name = QLabel(package.get('name', 'Package'))
        name.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        name.setStyleSheet("color: #111827; margin-bottom: 6px; padding: 0;")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)

        # Description with better readability
        desc = QLabel(package.get('description', ''))
        desc.setFont(QFont("Segoe UI", 13))
        desc.setStyleSheet("color: #6B7280; line-height: 1.6; padding: 0;")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setMinimumHeight(52)
        desc.setMaximumHeight(66)

        # Value proposition section with improved design
        value_container = QFrame()
        value_container.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
            }
        """)
        value_layout = QVBoxLayout(value_container)
        value_layout.setContentsMargins(20, 18, 20, 18)
        value_layout.setSpacing(14)

        # "What you get" header with better styling
        get_label = QLabel("✨ What you get")
        get_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        get_label.setStyleSheet("color: #374151; margin-bottom: 4px;")

        # Time benefit with prominent display
        time_minutes = package.get('minutes', 0)
        time_hours = time_minutes // 60
        if time_hours > 0:
            time_display = f"{time_hours}h {time_minutes % 60}m"
        else:
            time_display = f"{time_minutes} min"
        
        time_benefit = self.create_benefit_row("⏰", "Computing Time", time_display, package_tier['accent_color'])
        
        # Prints benefit
        prints = package.get('prints', 0)
        prints_benefit = self.create_benefit_row("🖨️", "Print Credits", f"{prints} prints", package_tier['accent_color'])

        value_layout.addWidget(get_label)
        value_layout.addWidget(time_benefit)
        value_layout.addWidget(prints_benefit)

        # Price section with better hierarchy and spacing
        price_container = QWidget()
        price_layout = QVBoxLayout(price_container)
        price_layout.setContentsMargins(0, 12, 0, 12)
        price_layout.setSpacing(6)
        price_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pricing = self.package_service.calculate_final_price(package)

        if pricing['discount_percent'] > 0:
            # Discount badge with better styling
            discount_badge = QLabel(f"SAVE {pricing['discount_percent']:.0f}%")
            discount_badge.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            discount_badge.setStyleSheet("""
                color: #DC2626;
                background-color: #FEF2F2;
                border: 1px solid #FECACA;
                padding: 6px 16px;
                border-radius: 20px;
            """)
            discount_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            discount_badge.setMaximumHeight(28)

            # Original price (strikethrough) - larger and clearer
            original_label = QLabel(f"₪{pricing['original_price']:.0f}")
            original_label.setFont(QFont("Segoe UI", 16))
            original_label.setStyleSheet("color: #9CA3AF; text-decoration: line-through;")
            original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Final price - hero element, much larger
            final_label = QLabel(f"₪{pricing['final_price']:.0f}")
            final_label.setFont(QFont("Segoe UI", 44, QFont.Weight.Bold))
            final_label.setStyleSheet(f"color: {package_tier['accent_color']}; padding: 6px;")
            final_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            final_label.setMinimumHeight(55)

            price_layout.addWidget(discount_badge)
            price_layout.addWidget(original_label)
            price_layout.addWidget(final_label)
        else:
            # Just final price - hero element, very large and clear
            final_label = QLabel(f"₪{pricing['final_price']:.0f}")
            final_label.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
            final_label.setStyleSheet("color: #1F2937; padding: 8px;")
            final_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            final_label.setMinimumHeight(60)
            price_layout.addWidget(final_label)

        # Enhanced purchase button with modern styling
        purchase_btn = QPushButton("GET THIS PACKAGE")
        purchase_btn.setObjectName("purchaseButton")
        purchase_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        purchase_btn.setMinimumHeight(58)
        purchase_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        purchase_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {package_tier['accent_color']};
                color: white;
                border: none;
                border-radius: 28px;
                padding: 16px 32px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {package_tier['hover_color']};
            }}
            QPushButton:pressed {{
                background-color: {package_tier['pressed_color']};
            }}
        """)
        purchase_btn.clicked.connect(lambda: self.handle_purchase(package))

        # Assembly
        content_layout.addWidget(name)
        content_layout.addWidget(desc)
        content_layout.addWidget(value_container)
        content_layout.addWidget(price_container)
        content_layout.addStretch()
        content_layout.addWidget(purchase_btn)

        layout.addWidget(header)
        layout.addWidget(content)

        return card

    def create_benefit_row(self, icon: str, label: str, value: str, accent_color: str) -> QWidget:
        """Create a benefit row with icon, label and value - improved readability"""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(14)

        # Icon with better sizing
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 18))
        icon_label.setFixedSize(28, 28)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Label with better typography
        label_widget = QLabel(label)
        label_widget.setFont(QFont("Segoe UI", 12))
        label_widget.setStyleSheet("color: #4B5563; font-weight: 500;")

        # Value (prominent and larger)
        value_widget = QLabel(value)
        value_widget.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        value_widget.setStyleSheet(f"color: {accent_color}; padding: 2px;")

        row_layout.addWidget(icon_label)
        row_layout.addWidget(label_widget)
        row_layout.addStretch()
        row_layout.addWidget(value_widget)

        return row

    def get_package_tier(self, package: Dict) -> Dict:
        """Determine package tier for styling"""
        name = package.get('name', '').lower()
        
        # Define tier characteristics
        if 'power' in name or 'all-day' in name:
            return {
                'accent_color': '#7C3AED',  # Purple
                'hover_color': '#6D28D9',
                'pressed_color': '#5B21B6',
                'is_popular': 'power' in name
            }
        elif 'standard' in name:
            return {
                'accent_color': '#2563EB',  # Blue
                'hover_color': '#1D4ED8',
                'pressed_color': '#1E40AF',
                'is_popular': True
            }
        elif 'student' in name:
            return {
                'accent_color': '#059669',  # Green
                'hover_color': '#047857',
                'pressed_color': '#065F46',
                'is_popular': False
            }
        else:
            return {
                'accent_color': '#DC2626',  # Red
                'hover_color': '#B91C1C',
                'pressed_color': '#991B1B',
                'is_popular': False
            }

    def handle_purchase(self, package: Dict):
        """Handle package purchase"""
        logger.info(f"Purchase initiated: {package.get('name')}")

        from ui.payment_dialog import PaymentDialog
        from services.purchase_service import PurchaseService
        from PyQt6.QtWidgets import QMessageBox

        # Open payment dialog (derive user and auth from parent)
        dialog = PaymentDialog(package, self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # Payment successful
            payment_response = dialog.get_payment_response()

            if not payment_response:
                # Get parent window to show dialog
                parent_window = self.window()
                if hasattr(parent_window, 'show_error'):
                    parent_window.show_error("Payment Error", "Payment confirmation not received")
                else:
                    QMessageBox.critical(self, "שגיאה", "לא התקבל אישור תשלום")
                return

            # Record purchase and credit account
            purchase_service = PurchaseService(self.auth_service.firebase)
            purchase_result = purchase_service.record_purchase(
                self.current_user['uid'],
                package,
                payment_response
            )

            if purchase_result.get('success'):
                # Update local user data
                self.current_user['remainingTime'] = purchase_result['new_time']
                self.current_user['remainingPrints'] = purchase_result['new_prints']

                # Show success with modern dialog
                parent_window = self.window()
                if hasattr(parent_window, 'show_success'):
                    parent_window.show_success(
                        "Purchase Complete! 🎉",
                        f"Your purchase was successful!",
                        f"Added to your account:<br>"
                        f"• <b>{package.get('minutes')} minutes</b> of session time<br>"
                        f"• <b>{package.get('prints')} prints</b>"
                    )
                else:
                    QMessageBox.information(
                        self,
                        "רכישה הושלמה",
                        f"הרכישה בוצעה בהצלחה!\n\n"
                        f"נוספו לחשבונך:\n"
                        f"• {package.get('minutes')} דקות\n"
                        f"• {package.get('prints')} הדפסות"
                    )

                # Refresh packages page
                self.load_packages()
            else:
                parent_window = self.window()
                if hasattr(parent_window, 'show_error'):
                    parent_window.show_error(
                        "Account Update Failed",
                        "Payment was processed but account update failed",
                        purchase_result.get('error', 'Unknown error')
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "שגיאה",
                        f"התשלום בוצע אך נכשל עדכון החשבון.\n{purchase_result.get('error')}"
                    )
        else:
            # Payment cancelled
            logger.info("Payment cancelled by user")


class HoverFrame(QFrame):
    """QFrame that subtly enhances elevation on hover for modern UX"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(30)
        self._shadow.setXOffset(0)
        self._shadow.setYOffset(6)
        self._shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(self._shadow)

        # Enable hover events
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def enterEvent(self, event):
        # Intensify elevation on hover
        if isinstance(self.graphicsEffect(), QGraphicsDropShadowEffect):
            eff: QGraphicsDropShadowEffect = self.graphicsEffect()
            eff.setBlurRadius(40)
            eff.setYOffset(10)
            eff.setColor(QColor(0, 0, 0, 60))
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Restore elevation
        if isinstance(self.graphicsEffect(), QGraphicsDropShadowEffect):
            eff: QGraphicsDropShadowEffect = self.graphicsEffect()
            eff.setBlurRadius(30)
            eff.setYOffset(6)
            eff.setColor(QColor(0, 0, 0, 40))
        super().leaveEvent(event)