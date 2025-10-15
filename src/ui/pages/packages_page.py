"""
Packages Page
Browse and purchase time/print packages
"""

from typing import Dict
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                             QPushButton, QFrame, QGridLayout,
                             QScrollArea, QDialog, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from services.package_service import PackageService
from utils.logger import get_logger

logger = get_logger(__name__)


class PackagesPage(QWidget):
    """Packages browser and purchase page"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.current_user = None  # Will be set when page is shown
        self.package_service = PackageService(auth_service.firebase)

        self.packages = []

        self.init_ui()
        self.load_packages()

    def init_ui(self):
        """Initialize beautiful modern UI"""
        # Set RTL layout direction for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.setStyleSheet("""
            QWidget {
                background: #F1F5F9;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(30)

        # Clean header section
        header_container = QWidget()
        header_container.setStyleSheet("""
            QWidget {
                background: #3B82F6;
                border-radius: 20px;
                padding: 20px;
            }
        """)
        
        # Add shadow to header
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(40)
        header_shadow.setXOffset(0)
        header_shadow.setYOffset(12)
        header_shadow.setColor(QColor(0, 0, 0, 55))
        header_container.setGraphicsEffect(header_shadow)
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(30, 25, 30, 25)
        header_layout.setSpacing(8)

        # Main title with stunning typography
        title = QLabel("חבילות זמינות")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: 800;
                margin-bottom: 8px;
            }
        """)

        # Subtitle with elegant styling
        subtitle = QLabel("רכוש זמן נוסף וקרדיטי הדפסה")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                font-weight: 400;
            }
        """)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        # Packages grid container with modern styling
        self.packages_container = QWidget()
        self.packages_container.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        self.packages_layout = QGridLayout(self.packages_container)
        self.packages_layout.setSpacing(25)
        self.packages_layout.setContentsMargins(20, 20, 20, 20)
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logger.info("Created packages grid layout")

        # Beautiful scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.packages_container)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setMinimumHeight(500)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #E2E8F0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #94A3B8;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #64748B;
            }
        """)

        # Loading/empty state label with beautiful styling
        self.state_label = QLabel("טוען חבילות...")
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 18px;
                font-weight: 500;
                padding: 40px;
                background: white;
                border-radius: 16px;
                border: 2px dashed #E2E8F0;
            }
        """)

        main_layout.addWidget(header_container)
        main_layout.addWidget(self.state_label)
        main_layout.addWidget(scroll, 1)

        logger.debug("Packages page initialized with modern styling")

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
        logger.info(f"Packages data: {self.packages}")
        
        # Hide loading label and show packages
        self.state_label.hide()
        logger.info("About to call display_packages()")
        self.display_packages()

    def refresh_user_data(self):
        """Refresh user data and reload packages"""
        logger.info("Refreshing user data in PackagesPage")
        
        # Get current user from auth service
        self.current_user = self.auth_service.get_current_user()
        
        # Don't reload packages here - they're already loaded during initialization
        # This prevents duplicate package loading

    def clear_user_data(self):
        """Clear all user data (called on logout)"""
        logger.info("Clearing user data in PackagesPage")
        
        self.current_user = None
        self.packages = []
        
        # Show empty state
        self.state_label.setText("📦 אין חבילות זמינות")
        self.state_label.show()

    def display_packages(self):
        """Display packages in beautiful responsive grid"""
        logger.info(f"Displaying {len(self.packages)} packages")
        
        # Clear existing widgets
        for i in reversed(range(self.packages_layout.count())):
            widget = self.packages_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Calculate optimal columns based on screen width (responsive design)
        max_columns = 3  # Default for desktop
        if len(self.packages) == 1:
            max_columns = 1
        elif len(self.packages) == 2:
            max_columns = 2
        elif len(self.packages) <= 4:
            max_columns = 2

        # Display packages in grid
        row, col = 0, 0
        
        # Filter out invalid packages before displaying
        valid_packages = []
        for package in self.packages:
            if isinstance(package, dict) and 'name' in package:
                valid_packages.append(package)
            else:
                logger.warning(f"Skipping invalid package: {package} (type: {type(package)})")
        
        logger.info(f"Found {len(valid_packages)} valid packages out of {len(self.packages)} total")
        
        if len(valid_packages) == 0:
            logger.warning("No valid packages to display")
            return

        for package in valid_packages:
            logger.info(f"Creating card for package: {package.get('name', 'Unknown')}")
            card = self.create_package_card(package)
            
            # Add card to grid with proper alignment
            self.packages_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignCenter)
            logger.info(f"Added card to grid at row {row}, col {col}")

            col += 1
            if col >= max_columns:
                col = 0
                row += 1
        
        logger.info(f"Finished displaying packages. Grid has {self.packages_layout.count()} items")
        
        # Force UI refresh and repaint
        self.packages_container.update()
        self.packages_container.repaint()
        self.update()
        self.repaint()

    def create_package_card(self, package: Dict) -> QFrame:
        """Create a clean, simple package card - no tier logic"""
        # Validate package data
        if not isinstance(package, dict):
            logger.error(f"Invalid package data: {package} (type: {type(package)})")
            return QFrame()  # Return empty frame for invalid data
        
        logger.info(f"Creating card for: {package.get('name', 'Unknown')}")
        
        # Main card container - clean and simple
        card = QFrame()
        card.setFixedSize(320, 480)  # Perfect card dimensions
        card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 20px;
                border: 2px solid #E2E8F0;
            }
            QFrame:hover {
                border: 2px solid #3B82F6;
                background: #F8FAFC;
            }
        """)
        
        # Add beautiful drop shadow for depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setXOffset(0)
        shadow.setYOffset(18)
        shadow.setColor(QColor(0, 0, 0, 65))
        card.setGraphicsEffect(shadow)

        # Main layout with perfect spacing
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Package name with beautiful typography
        name = QLabel(package.get('name', 'חבילה'))
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)
        name.setStyleSheet("""
            QLabel {
                color: #1E293B;
                font-size: 24px;
                font-weight: 700;
                line-height: 1.2;
                margin-bottom: 8px;
            }
        """)

        # Description with elegant styling
        desc = QLabel(package.get('description', 'תיאור החבילה'))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("""
            QLabel {
                color: #64748B;
                font-size: 14px;
                font-weight: 400;
                line-height: 1.4;
                margin-bottom: 16px;
            }
        """)

        # Elegant separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("""
            QFrame {
                color: #E2E8F0;
                background-color: #E2E8F0;
                border: none;
                height: 1px;
                margin: 8px 0;
            }
        """)

        # Features container - simplified and always visible
        features_container = QWidget()
        features_layout = QVBoxLayout(features_container)
        features_layout.setContentsMargins(0, 0, 0, 0)
        features_layout.setSpacing(12)

        # Time feature - always display
        time_minutes = package.get('minutes', 0)
        hours = time_minutes // 60
        mins = time_minutes % 60
        time_text = f"⏰ {hours}:{mins:02d} שעות" if time_minutes > 0 else "⏰ ללא הגבלת זמן"
        time_label = QLabel(time_text)
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_label.setStyleSheet("""
            QLabel {
                background-color: #F1F5F9;
                color: #475569;
                font-size: 15px;
                font-weight: 600;
                padding: 12px 16px;
                border-radius: 12px;
                border-left: 4px solid #3B82F6;
            }
        """)
        
        # Prints feature - always display
        prints = package.get('prints', 0)
        prints_text = f"🖨️ {prints} הדפסות" if prints > 0 else "🖨️ ללא הגבלת הדפסות"
        prints_label = QLabel(prints_text)
        prints_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prints_label.setStyleSheet("""
            QLabel {
                background-color: #F0FDF4;
                color: #166534;
                font-size: 15px;
                font-weight: 600;
                padding: 12px 16px;
                border-radius: 12px;
                border-left: 4px solid #10B981;
            }
        """)

        features_layout.addWidget(time_label)
        features_layout.addWidget(prints_label)

        # Price section - completely simplified
        price_container = QWidget()
        price_layout = QVBoxLayout(price_container)
        price_layout.setContentsMargins(0, 20, 0, 20)
        price_layout.setSpacing(8)

        # Simple price display - no tier logic
        price = package.get('price', 0)
        price_label = QLabel(f"₪{price}")
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet("""
            QLabel {
                color: #1E40AF;
                font-size: 36px;
                font-weight: 800;
            }
        """)
        price_layout.addWidget(price_label)

        # Clean purchase button
        purchase_btn = QPushButton("קנה עכשיו")
        purchase_btn.setMinimumHeight(52)
        purchase_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        purchase_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6;
                color: white;
                font-size: 16px;
                font-weight: 700;
                border: none;
                border-radius: 16px;
                padding: 16px 24px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background: #2563EB;
            }
            QPushButton:pressed {
                background: #1D4ED8;
            }
        """)
        purchase_btn.clicked.connect(lambda: self.handle_purchase(package))

        # Assemble the card
        layout.addWidget(name)
        layout.addWidget(desc)
        layout.addWidget(separator)
        layout.addWidget(features_container)
        layout.addStretch()  # Push price and button to bottom
        layout.addWidget(price_container)
        layout.addWidget(purchase_btn)

        logger.info(f"Card created successfully for: {package.get('name', 'Unknown')}")
        return card



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

            # Payment was successful - the purchase is already recorded by the Cloud Function
            # The user's account has been credited automatically
            logger.info("Payment completed successfully - user account credited by Cloud Function")
            
            # Show success message
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
            # Payment cancelled
            logger.info("Payment cancelled by user")

