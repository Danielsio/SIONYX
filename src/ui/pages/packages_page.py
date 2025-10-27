"""
Packages Page - FROST Design System
Modern package cards with clean grid layout.
"""

from typing import Dict

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.services.package_service import PackageService
from src.utils.logger import get_logger
from ui.components.base_components import (
    ActionButton,
    EmptyState,
    LoadingSpinner,
    PageHeader,
    apply_shadow,
)
from ui.constants.ui_constants import (
    BorderRadius,
    Colors,
    Dimensions,
    Gradients,
    Spacing,
    Typography,
    UIStrings,
)

logger = get_logger(__name__)


class PackagesPage(QWidget):
    """Modern packages browser with grid layout"""

    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.current_user = None
        self.package_service = PackageService(auth_service.firebase)
        self.packages = []

        self.init_ui()
        self.load_packages()

    def init_ui(self):
        """Build the UI"""
        self.setObjectName("packagesPage")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(f"background: {Colors.BG_PAGE};")

        # Center content
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        content.setMaximumWidth(1100)  # Wider to accommodate card shadows
        content.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        layout.setSpacing(Spacing.LG)

        # Header
        header = PageHeader(UIStrings.PACKAGES_TITLE, UIStrings.PACKAGES_SUBTITLE)
        layout.addWidget(header)

        # Packages grid - extra padding for shadows
        self.packages_container = QWidget()
        self.packages_container.setStyleSheet("background: transparent;")
        self.packages_layout = QGridLayout(self.packages_container)
        self.packages_layout.setSpacing(Spacing.LG)
        self.packages_layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.XL)
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Scroll area - with room for shadows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.packages_container)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMinimumHeight(480)
        # Important: Don't clip shadows
        scroll.viewport().setStyleSheet("background: transparent;")
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.GRAY_300};
                border-radius: 4px;
                min-height: 40px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Colors.GRAY_400};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        # Loading spinner
        self.loading_spinner = LoadingSpinner("טוען חבילות...")
        layout.addWidget(self.loading_spinner)
        layout.addSpacing(Spacing.SM)  # Space after header for floating effect
        layout.addWidget(scroll, 1)

        outer.addStretch()
        outer.addWidget(content)
        outer.addStretch()

    def load_packages(self):
        """Load packages from Firebase"""
        QTimer.singleShot(300, self._fetch_packages)

    def _fetch_packages(self):
        """Fetch packages from service"""
        result = self.package_service.get_all_packages()

        if not result.get("success"):
            self.loading_spinner.hide()
            self._show_error()
            return

        self.packages = result.get("data", [])
        self.loading_spinner.hide()

        if not self.packages:
            self._show_empty()
            return

        self._display_packages()

    def _show_error(self):
        """Show error state"""
        self._clear_grid()
        error = EmptyState("❌", "שגיאה בטעינה", "לא הצלחנו לטעון את החבילות")
        self.packages_layout.addWidget(error, 0, 0)

    def _show_empty(self):
        """Show empty state"""
        self._clear_grid()
        empty = EmptyState("📦", "אין חבילות זמינות", "נסה שוב מאוחר יותר")
        self.packages_layout.addWidget(empty, 0, 0)

    def _clear_grid(self):
        """Clear the packages grid"""
        for i in reversed(range(self.packages_layout.count())):
            widget = self.packages_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def _display_packages(self):
        """Display packages in grid"""
        self._clear_grid()

        # Calculate columns
        cols = min(3, len(self.packages)) if len(self.packages) > 2 else len(self.packages)

        row, col = 0, 0
        for package in self.packages:
            if isinstance(package, dict) and "name" in package:
                card = self._create_package_card(package)
                self.packages_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignCenter)

                col += 1
                if col >= cols:
                    col = 0
                    row += 1

    def _create_package_card(self, package: Dict) -> QFrame:
        """Create a modern package card"""
        card = QFrame()
        card.setFixedSize(280, 400)
        card.setStyleSheet(f"""
            QFrame {{
                background: {Colors.WHITE};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: {BorderRadius.XL}px;
            }}
            QFrame:hover {{
                border-color: {Colors.PRIMARY};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        apply_shadow(card, "md")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        # Package name
        name = QLabel(package.get("name", "חבילה"))
        name.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_XL, Typography.WEIGHT_BOLD))
        name.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)
        layout.addWidget(name)

        # Description
        desc = QLabel(package.get("description", ""))
        desc.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_SM))
        desc.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setMaximumHeight(40)
        layout.addWidget(desc)

        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background: {Colors.BORDER_LIGHT};")
        layout.addWidget(divider)

        # Features
        features = QWidget()
        features_layout = QVBoxLayout(features)
        features_layout.setContentsMargins(0, 0, 0, 0)
        features_layout.setSpacing(Spacing.SM)

        # Time
        minutes = package.get("minutes", 0)
        hours = minutes // 60
        mins = minutes % 60
        time_text = f"⏱️  {hours}:{mins:02d} שעות" if minutes > 0 else "⏱️  ללא הגבלה"
        time_lbl = self._create_feature_label(time_text, Colors.PRIMARY)
        features_layout.addWidget(time_lbl)

        # Prints
        prints = package.get("prints", 0)
        prints_text = f"🖨️  {prints}₪ יתרת הדפסות" if prints > 0 else "🖨️  ללא הגבלה"
        prints_lbl = self._create_feature_label(prints_text, Colors.ACCENT)
        features_layout.addWidget(prints_lbl)

        layout.addWidget(features)
        layout.addStretch()

        # Price
        price = package.get("price", 0)
        price_lbl = QLabel(f"₪{price}")
        price_lbl.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_3XL, Typography.WEIGHT_EXTRABOLD))
        price_lbl.setStyleSheet(f"color: {Colors.PRIMARY};")
        price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(price_lbl)

        # Buy button
        buy_btn = ActionButton(UIStrings.BUY_NOW, "primary", "md")
        buy_btn.clicked.connect(lambda: self._handle_purchase(package))
        layout.addWidget(buy_btn)

        return card

    def _create_feature_label(self, text: str, color: str) -> QLabel:
        """Create a feature label with icon"""
        label = QLabel(text)
        label.setFont(QFont(Typography.FONT_FAMILY, Typography.SIZE_SM, Typography.WEIGHT_MEDIUM))
        label.setStyleSheet(f"""
            background: {color}15;
            color: {color};
            padding: {Spacing.SM}px {Spacing.MD}px;
            border-radius: {BorderRadius.SM}px;
            border-right: 3px solid {color};
        """)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def _handle_purchase(self, package: Dict):
        """Handle package purchase"""
        logger.info(f"Purchase initiated: {package.get('name')}")

        from PyQt6.QtWidgets import QMessageBox
        from ui.payment_dialog import PaymentDialog

        dialog = PaymentDialog(package, self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            response = dialog.get_payment_response()
            if response:
                logger.info("Payment completed successfully")
                self._show_success(package)
                self.load_packages()
            else:
                self._show_payment_error()
        else:
            logger.info("Payment cancelled")

    def _show_success(self, package: Dict):
        """Show success message"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "רכישה הושלמה! 🎉",
            f"הרכישה בוצעה בהצלחה!\n\n"
            f"נוספו לחשבונך:\n"
            f"• {package.get('minutes')} דקות\n"
            f"• {package.get('prints')}₪ יתרת הדפסות"
        )

    def _show_payment_error(self):
        """Show payment error"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.critical(self, "שגיאה", "לא התקבל אישור תשלום")

    def refresh_user_data(self):
        """Refresh user data"""
        self.current_user = self.auth_service.get_current_user()

    def clear_user_data(self):
        """Clear user data"""
        self.current_user = None
        self.packages = []
        self._clear_grid()
