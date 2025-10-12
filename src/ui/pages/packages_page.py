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
        
        # Set RTL layout direction for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(45, 35, 45, 35)
        main_layout.setSpacing(25)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("חבילות זמינות")
        title.setFont(QFont("Segoe UI", 30, QFont.Weight.Bold))
        title.setStyleSheet("color: #111827;")

        subtitle = QLabel("רכוש זמן נוסף וקרדיטי הדפסה")
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setStyleSheet("color: #6B7280;")

        header_container = QWidget()
        header_container.setStyleSheet("background-color: transparent;")
        header_vlayout = QVBoxLayout(header_container)
        header_vlayout.setContentsMargins(0, 0, 0, 0)
        header_vlayout.setSpacing(5)
        header_vlayout.addWidget(title)
        header_vlayout.addWidget(subtitle)

        header_layout.addWidget(header_container)
        header_layout.addStretch()

        # Packages grid container (will be populated after load)
        self.packages_container = QWidget()
        self.packages_container.setStyleSheet("background-color: transparent;")
        self.packages_layout = QGridLayout(self.packages_container)
        self.packages_layout.setSpacing(20)
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        scroll.setWidget(self.packages_container)

        # Loading/empty state label
        self.state_label = QLabel("טוען חבילות...")
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
            self.state_label.setText("❌ נכשל בטעינת החבילות")
            return

        self.packages = result.get('packages', [])

        if len(self.packages) == 0:
            logger.warning("No packages available")
            self.state_label.setText("📦 אין חבילות זמינות עדיין")
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
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the grid

        # Display in grid (adjust columns for larger 380px cards)
        row, col = 0, 0
        max_columns = 3  # Can still fit 3 cards with new spacing
        
        for package in self.packages:
            card = self.create_package_card(package)
            self.packages_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignCenter)

            col += 1
            if col >= max_columns:
                col = 0
                row += 1

    def create_package_card(self, package: Dict) -> QFrame:
        """Create a clean, modern package card"""
        card = HoverFrame()
        card.setObjectName("packageCard")
        card.setFixedSize(400, 680)  # Reduced from 820 to fit content better
        
        # Clean card styling
        card.setStyleSheet("""
            QFrame#packageCard {
                background-color: white;
                border-radius: 24px;
                border: 1px solid #E2E8F0;
            }
        """)
        
        # Enhanced shadow for better depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(15, 23, 42, 60))  # Darker shadow for better contrast
        card.setGraphicsEffect(shadow)

        # Main layout
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Content container
        content = QWidget()
        content.setStyleSheet("background-color: white; border-radius: 24px;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 30, 32, 30)
        content_layout.setSpacing(20)

        # Get pricing info to determine if it's a hot deal
        pricing = self.package_service.calculate_final_price(package)
        is_hot_deal = pricing['discount_percent'] >= 15  # 15% or more = Hot Deal

        # Hot Deal badge
        if is_hot_deal:
            badge = QLabel("🔥 עסקה חמה")
            badge.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            badge.setStyleSheet("""
                color: white;
                background-color: #EF4444;
                padding: 8px 18px;
                border-radius: 20px;
            """)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setMaximumHeight(34)
            content_layout.addWidget(badge)

        # Package name
        name = QLabel(package.get('name', 'Package'))
        name.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        name.setStyleSheet("color: #111827;")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)
        name.setMinimumHeight(40)
        name.setMaximumHeight(50)

        # Description
        desc = QLabel(package.get('description', ''))
        desc.setFont(QFont("Segoe UI", 14))
        desc.setStyleSheet("color: #6B7280; line-height: 1.4;")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setMinimumHeight(45)
        desc.setMaximumHeight(60)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #E5E7EB; max-height: 1px;")

        # Time and Prints section
        benefits_container = QWidget()
        benefits_layout = QVBoxLayout(benefits_container)
        benefits_layout.setContentsMargins(0, 0, 0, 0)
        benefits_layout.setSpacing(14)

        # Time display
        time_minutes = package.get('minutes', 0)
        if time_minutes >= 60:
            hours = time_minutes // 60
            mins = time_minutes % 60
            time_text = f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
        else:
            time_text = f"{time_minutes} min"
        
        time_widget = self.create_clean_benefit("⏰", "זמן מחשוב", time_text)
        
        # Prints display
        prints = package.get('prints', 0)
        prints_widget = self.create_clean_benefit("🖨️", "קרדיטי הדפסה", f"{prints} הדפסות")

        benefits_layout.addWidget(time_widget)
        benefits_layout.addWidget(prints_widget)

        # Price section
        price_container = QWidget()
        price_layout = QVBoxLayout(price_container)
        price_layout.setContentsMargins(0, 20, 0, 20)
        price_layout.setSpacing(10)
        price_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if pricing['discount_percent'] > 0:
            # Discount badge
            discount_badge = QLabel(f"חיסכון {pricing['discount_percent']:.0f}%")
            discount_badge.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            discount_badge.setStyleSheet("""
                color: #DC2626;
                background-color: #FEF2F2;
                border: 2px solid #FECACA;
                padding: 8px 20px;
                border-radius: 24px;
            """)
            discount_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            discount_badge.setMaximumHeight(32)

            # Original price
            original_label = QLabel(f"₪{pricing['original_price']:.0f}")
            original_label.setFont(QFont("Segoe UI", 18))
            original_label.setStyleSheet("color: #9CA3AF; text-decoration: line-through;")
            original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Final price
            final_label = QLabel(f"₪{pricing['final_price']:.0f}")
            final_label.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
            final_label.setStyleSheet("color: #2563EB;")
            final_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            final_label.setMinimumHeight(60)

            price_layout.addWidget(discount_badge)
            price_layout.addWidget(original_label)
            price_layout.addWidget(final_label)
        else:
            # Just final price
            final_label = QLabel(f"₪{pricing['final_price']:.0f}")
            final_label.setFont(QFont("Segoe UI", 52, QFont.Weight.Bold))
            final_label.setStyleSheet("color: #111827;")
            final_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            final_label.setMinimumHeight(65)
            price_layout.addWidget(final_label)

        # Purchase button
        purchase_btn = QPushButton("קבל את החבילה הזו")
        purchase_btn.setObjectName("purchaseButton")
        purchase_btn.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        purchase_btn.setMinimumHeight(56)
        purchase_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Button color based on hot deal status
        btn_color = "#EF4444" if is_hot_deal else "#2563EB"
        btn_hover = "#DC2626" if is_hot_deal else "#1D4ED8"
        btn_pressed = "#B91C1C" if is_hot_deal else "#1E40AF"
        
        purchase_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_color};
                color: white;
                border: none;
                border-radius: 32px;
                padding: 18px 36px;
            }}
            QPushButton:hover {{
                background-color: {btn_hover};
            }}
            QPushButton:pressed {{
                background-color: {btn_pressed};
            }}
        """)
        purchase_btn.clicked.connect(lambda: self.handle_purchase(package))

        # Assembly
        content_layout.addWidget(name)
        content_layout.addWidget(desc)
        content_layout.addWidget(separator)
        content_layout.addWidget(benefits_container)
        content_layout.addWidget(price_container)
        content_layout.addStretch()
        content_layout.addWidget(purchase_btn)

        layout.addWidget(content)

        return card

    def create_clean_benefit(self, icon: str, label: str, value: str) -> QWidget:
        """Create a clean benefit display"""
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border-radius: 16px;
                padding: 4px;
            }
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI", 24))
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Label and value container
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        label_widget = QLabel(label)
        label_widget.setFont(QFont("Segoe UI", 13))
        label_widget.setStyleSheet("color: #6B7280;")

        value_widget = QLabel(value)
        value_widget.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        value_widget.setStyleSheet("color: #111827;")

        text_layout.addWidget(label_widget)
        text_layout.addWidget(value_widget)

        layout.addWidget(icon_label)
        layout.addWidget(text_container)
        layout.addStretch()

        return container


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
                    parent_window.show_error("שגיאת תשלום", "לא התקבל אישור תשלום")
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
                        "הרכישה הושלמה! 🎉",
                        f"הרכישה שלך בוצעה בהצלחה!",
                        f"נוסף לחשבונך:<br>"
                        f"• <b>{package.get('minutes')} דקות</b> של זמן הפעלה<br>"
                        f"• <b>{package.get('prints')} הדפסות</b>"
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
                        "נכשל עדכון החשבון",
                        "התשלום בוצע אך נכשל עדכון החשבון",
                        purchase_result.get('error', 'שגיאה לא ידועה')
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
        self._shadow.setBlurRadius(40)
        self._shadow.setXOffset(0)
        self._shadow.setYOffset(8)
        self._shadow.setColor(QColor(15, 23, 42, 60))
        self.setGraphicsEffect(self._shadow)

        # Enable hover events
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def enterEvent(self, event):
        # Intensify elevation on hover
        if isinstance(self.graphicsEffect(), QGraphicsDropShadowEffect):
            eff: QGraphicsDropShadowEffect = self.graphicsEffect()
            eff.setBlurRadius(50)
            eff.setYOffset(12)
            eff.setColor(QColor(15, 23, 42, 80))
        super().enterEvent(event)

    def leaveEvent(self, event):
        # Restore elevation
        if isinstance(self.graphicsEffect(), QGraphicsDropShadowEffect):
            eff: QGraphicsDropShadowEffect = self.graphicsEffect()
            eff.setBlurRadius(40)
            eff.setYOffset(8)
            eff.setColor(QColor(15, 23, 42, 60))
        super().leaveEvent(event)