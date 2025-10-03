"""
Packages Page
Browse and purchase time/print packages
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QFrame, QGridLayout, QMessageBox,
                              QGraphicsDropShadowEffect, QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from services.package_service import PackageService
from utils.logger import get_logger

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
        """Display packages in grid"""
        # Clear existing
        for i in reversed(range(self.packages_layout.count())):
            self.packages_layout.itemAt(i).widget().setParent(None)

        # Display in grid (3 columns)
        row, col = 0, 0
        for package in self.packages:
            card = self.create_package_card(package)
            self.packages_layout.addWidget(card, row, col)

            col += 1
            if col >= 3:
                col = 0
                row += 1

    def create_package_card(self, package: Dict) -> QFrame:
        """Create package display card"""
        card = QFrame()
        card.setObjectName("packageCard")
        card.setFixedSize(280, 320)

        # Shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Package name
        name = QLabel(package.get('name', 'Package'))
        name.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        name.setStyleSheet("color: #111827;")
        name.setWordWrap(True)

        # Description
        desc = QLabel(package.get('description', ''))
        desc.setFont(QFont("Segoe UI", 11))
        desc.setStyleSheet("color: #6B7280;")
        desc.setWordWrap(True)
        desc.setMaximumHeight(50)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #E5E7EB;")
        divider.setFixedHeight(1)

        # Includes
        includes_label = QLabel("Includes:")
        includes_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        includes_label.setStyleSheet("color: #9CA3AF;")

        # Time
        time_minutes = package.get('minutes', 0)
        time_hours = time_minutes // 60
        time_label = QLabel(f"⏱  {time_hours}h {time_minutes % 60}m" if time_hours > 0 else f"⏱  {time_minutes} min")
        time_label.setFont(QFont("Segoe UI", 11))
        time_label.setStyleSheet("color: #374151;")

        # Prints
        prints = package.get('prints', 0)
        prints_label = QLabel(f"🖨  {prints} prints")
        prints_label.setFont(QFont("Segoe UI", 11))
        prints_label.setStyleSheet("color: #374151;")

        # Price calculation
        pricing = self.package_service.calculate_final_price(package)

        # Price container
        price_container = QWidget()
        price_layout = QVBoxLayout(price_container)
        price_layout.setContentsMargins(0, 5, 0, 0)
        price_layout.setSpacing(2)

        if pricing['discount_percent'] > 0:
            # Original price (strikethrough)
            original_label = QLabel(f"₪{pricing['original_price']:.0f}")
            original_label.setFont(QFont("Segoe UI", 12))
            original_label.setStyleSheet("color: #9CA3AF; text-decoration: line-through;")

            # Final price
            final_label = QLabel(f"₪{pricing['final_price']:.0f}")
            final_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
            final_label.setStyleSheet("color: #059669;")

            # Discount badge
            discount_badge = QLabel(f"🏷 {pricing['discount_percent']:.0f}% OFF")
            discount_badge.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            discount_badge.setStyleSheet("""
                color: #DC2626;
                background-color: #FEE2E2;
                padding: 4px 8px;
                border-radius: 6px;
            """)
            discount_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

            price_layout.addWidget(discount_badge)
            price_layout.addWidget(original_label)
            price_layout.addWidget(final_label)
        else:
            # Just final price
            final_label = QLabel(f"₪{pricing['final_price']:.0f}")
            final_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
            final_label.setStyleSheet("color: #111827;")
            price_layout.addWidget(final_label)

        # Purchase button
        purchase_btn = QPushButton("Purchase")
        purchase_btn.setObjectName("purchaseButton")
        purchase_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        purchase_btn.setMinimumHeight(45)
        purchase_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        purchase_btn.clicked.connect(lambda: self.handle_purchase(package))

        # Add to layout
        layout.addWidget(name)
        layout.addWidget(desc)
        layout.addWidget(divider)
        layout.addWidget(includes_label)
        layout.addWidget(time_label)
        layout.addWidget(prints_label)
        layout.addStretch()
        layout.addWidget(price_container)
        layout.addWidget(purchase_btn)

        return card

    def handle_purchase(self, package: Dict):
        """Handle package purchase"""
        logger.info(f"Purchase initiated: {package.get('name')}")

        pricing = self.package_service.calculate_final_price(package)

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Purchase Package")
        msg.setText(f"Purchase {package.get('name')}?")
        msg.setInformativeText(
            f"Price: ₪{pricing['final_price']:.2f}\n"
            f"You'll receive:\n"
            f"• {package.get('minutes')} minutes\n"
            f"• {package.get('prints')} prints\n\n"
            f"Payment integration coming soon!"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()