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
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from services.package_service import PackageService
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
from utils.logger import get_logger


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

        # Main layout - full width
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        main_layout.setSpacing(Spacing.LG)

        # Header - centered with room for shadow
        header_container = QWidget()
        header_container.setStyleSheet("background: transparent;")
        header_layout = QHBoxLayout(header_container)
        # Add padding for shadow to render properly (shadow extends ~20px)
        header_layout.setContentsMargins(Spacing.LG, Spacing.SM, Spacing.LG, Spacing.LG)
        header = PageHeader(UIStrings.PACKAGES_TITLE, UIStrings.PACKAGES_SUBTITLE)
        header.setMaximumWidth(1000)
        header_layout.addStretch()
        header_layout.addWidget(header)
        header_layout.addStretch()
        main_layout.addWidget(header_container)

        # Loading spinner
        self.loading_spinner = LoadingSpinner("טוען חבילות...")
        main_layout.addWidget(
            self.loading_spinner, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Packages container - uses HBoxLayout for proper centering
        self.packages_container = QWidget()
        self.packages_container.setStyleSheet("background: transparent;")
        self.packages_layout = QHBoxLayout(self.packages_container)
        self.packages_layout.setSpacing(Spacing.LG)
        self.packages_layout.setContentsMargins(
            Spacing.XL, Spacing.LG, Spacing.XL, Spacing.XL
        )
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Scroll area - with room for shadows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.packages_container)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setMinimumHeight(480)
        # Important: Don't clip shadows
        scroll.viewport().setStyleSheet("background: transparent;")
        scroll.setStyleSheet(
            f"""
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
            QScrollBar:horizontal {{
                background: transparent;
                height: 8px;
            }}
            QScrollBar::handle:horizontal {{
                background: {Colors.GRAY_300};
                border-radius: 4px;
                min-width: 40px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {Colors.GRAY_400};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
        """
        )

        main_layout.addSpacing(Spacing.SM)
        main_layout.addWidget(scroll, 1)

    def load_packages(self):
        """Load packages from Firebase"""
        QTimer.singleShot(300, self._fetch_packages)

    def _fetch_packages(self):
        """Fetch packages from service"""
        logger.debug("PackagesPage._fetch_packages called")
        result = self.package_service.get_all_packages()
        
        logger.debug(f"Package fetch result: success={result.get('success')}")

        if not result.get("success"):
            logger.error(f"Failed to fetch packages: {result.get('error')}")
            self.loading_spinner.hide()
            self._show_error()
            return

        self.packages = result.get("data", [])
        logger.info(f"PackagesPage: Received {len(self.packages)} packages to display")
        self.loading_spinner.hide()

        if not self.packages:
            logger.warning("No packages to display - showing empty state")
            self._show_empty()
            return

        logger.debug(f"Displaying {len(self.packages)} packages")
        self._display_packages()

    def _show_error(self):
        """Show error state"""
        self._clear_grid()
        error = EmptyState("❌", "שגיאה בטעינה", "לא הצלחנו לטעון את החבילות")
        self.packages_layout.addWidget(error, Qt.AlignmentFlag.AlignCenter)

    def _show_empty(self):
        """Show empty state"""
        self._clear_grid()
        empty = EmptyState("📦", "אין חבילות זמינות", "נסה שוב מאוחר יותר")
        self.packages_layout.addWidget(empty, Qt.AlignmentFlag.AlignCenter)

    def _clear_grid(self):
        """Clear the packages grid"""
        for i in reversed(range(self.packages_layout.count())):
            widget = self.packages_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

    def _display_packages(self):
        """Display packages in a centered horizontal row"""
        self._clear_grid()

        for package in self.packages:
            if isinstance(package, dict) and "name" in package:
                card = self._create_package_card(package)
                self.packages_layout.addWidget(card, Qt.AlignmentFlag.AlignCenter)

    def _create_package_card(self, package: Dict) -> QFrame:
        """Create a modern package card"""
        card = QFrame()
        card.setFixedSize(Dimensions.PACKAGE_CARD_WIDTH, Dimensions.PACKAGE_CARD_HEIGHT)
        card.setStyleSheet(
            f"""
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
        """
        )
        apply_shadow(card, "md")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        # Package name
        name = QLabel(package.get("name", "חבילה"))
        name.setFont(
            QFont(Typography.FONT_FAMILY, Typography.SIZE_XL, Typography.WEIGHT_BOLD)
        )
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

        # Features - only show features that have value (not 0)
        features = QWidget()
        features_layout = QVBoxLayout(features)
        features_layout.setContentsMargins(0, 0, 0, 0)
        features_layout.setSpacing(Spacing.SM)

        # Time - only show if package includes time
        minutes = package.get("minutes", 0)
        if minutes > 0:
            hours = minutes // 60
            mins = minutes % 60
            time_text = f"⏱️  {hours}:{mins:02d} שעות"
            time_lbl = self._create_feature_label(time_text, Colors.PRIMARY)
            features_layout.addWidget(time_lbl)

        # Prints - only show if package includes print balance
        prints = package.get("prints", 0)
        if prints > 0:
            prints_text = f"🖨️  {prints}₪ יתרת הדפסות"
            prints_lbl = self._create_feature_label(prints_text, Colors.ACCENT)
            features_layout.addWidget(prints_lbl)

        layout.addWidget(features)
        layout.addStretch(1)

        # Price (with discount if applicable)
        pricing = PackageService.calculate_final_price(package)
        final_price = pricing["final_price"]
        original_price = pricing["original_price"]
        discount_percent = pricing["discount_percent"]

        # Price container - give it minimum height to prevent cutoff
        price_container = QWidget()
        price_container.setMinimumHeight(80 if discount_percent > 0 else 50)
        price_layout = QVBoxLayout(price_container)
        price_layout.setContentsMargins(0, Spacing.SM, 0, Spacing.SM)
        price_layout.setSpacing(Spacing.XS)

        if discount_percent > 0:
            # Show original price crossed out
            original_price_lbl = QLabel(f"₪{original_price}")
            original_price_lbl.setFont(
                QFont(
                    Typography.FONT_FAMILY,
                    Typography.SIZE_BASE,
                    Typography.WEIGHT_MEDIUM,
                )
            )
            original_price_lbl.setStyleSheet(
                f"""
                color: {Colors.GRAY_500};
                text-decoration: line-through;
            """
            )
            original_price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_layout.addWidget(original_price_lbl)

            # Show final price
            final_price_lbl = QLabel(f"₪{final_price}")
            final_price_lbl.setFont(
                QFont(
                    Typography.FONT_FAMILY,
                    Typography.SIZE_2XL,
                    Typography.WEIGHT_EXTRABOLD,
                )
            )
            final_price_lbl.setStyleSheet(f"color: {Colors.SUCCESS};")
            final_price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_layout.addWidget(final_price_lbl)

            # Show discount badge
            discount_badge = QLabel(f"חסכון {int(discount_percent)}%")
            discount_badge.setFont(
                QFont(
                    Typography.FONT_FAMILY, Typography.SIZE_SM, Typography.WEIGHT_BOLD
                )
            )
            discount_badge.setStyleSheet(
                f"""
                color: {Colors.WHITE};
                background-color: {Colors.SUCCESS};
                padding: {Spacing.XS}px {Spacing.SM}px;
                border-radius: {BorderRadius.SM}px;
            """
            )
            discount_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_layout.addWidget(discount_badge)
        else:
            # No discount - just show the price
            price_lbl = QLabel(f"₪{final_price}")
            price_lbl.setFont(
                QFont(
                    Typography.FONT_FAMILY,
                    Typography.SIZE_3XL,
                    Typography.WEIGHT_EXTRABOLD,
                )
            )
            price_lbl.setStyleSheet(f"color: {Colors.PRIMARY};")
            price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            price_layout.addWidget(price_lbl)

        layout.addWidget(price_container)

        # Buy button
        buy_btn = ActionButton(UIStrings.BUY_NOW, "primary", "md")
        buy_btn.clicked.connect(lambda: self._handle_purchase(package))
        layout.addWidget(buy_btn)

        return card

    def _create_feature_label(self, text: str, color: str) -> QLabel:
        """Create a feature label with icon"""
        label = QLabel(text)
        label.setFont(
            QFont(Typography.FONT_FAMILY, Typography.SIZE_SM, Typography.WEIGHT_MEDIUM)
        )
        label.setStyleSheet(
            f"""
            background: {color}15;
            color: {color};
            padding: {Spacing.SM}px {Spacing.MD}px;
            border-radius: {BorderRadius.SM}px;
            border-right: 3px solid {color};
        """
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def _handle_purchase(self, package: Dict):
        """Handle package purchase"""
        logger.info(f"Purchase initiated: {package.get('name')}")

        from PyQt6.QtWidgets import QMessageBox

        from ui.payment_dialog import PaymentDialog

        try:
            dialog = PaymentDialog(package, self)
        except ValueError as e:
            logger.error(f"Failed to open payment dialog: {e}")
            QMessageBox.critical(
                self,
                "שגיאה",
                "לא ניתן לפתוח את חלון התשלום.\n"
                "נסה להתנתק ולהתחבר מחדש.",
            )
            return
        except Exception as e:
            logger.exception(f"Unexpected error opening payment dialog: {e}")
            QMessageBox.critical(
                self,
                "שגיאה",
                f"שגיאה לא צפויה: {e}",
            )
            return

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
            f"• {package.get('prints')}₪ יתרת הדפסות",
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
