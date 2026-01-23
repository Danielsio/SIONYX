"""
Packages Page - FROST Design System
Modern package cards with clean grid layout.
"""

from typing import Dict, Optional
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
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
        self._featured_package_id = None
        self.package_cards = []
        self._state_widget = None
        self._reflow_timer = QTimer(self)
        self._reflow_timer.setSingleShot(True)
        self._reflow_timer.timeout.connect(self._layout_packages)

        self.init_ui()
        self.load_packages()

    def init_ui(self):
        """Build the UI"""
        self.setObjectName("packagesPage")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(
            f"""
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 {Colors.BG_PAGE},
                stop:1 {Colors.GRAY_100}
            );
        """
        )

        # Main layout - full width
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.LG)
        main_layout.setSpacing(Spacing.LG)

        # Header - full width hero
        header = PageHeader(UIStrings.PACKAGES_TITLE, UIStrings.PACKAGES_SUBTITLE)
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        main_layout.addWidget(header)

        # Loading spinner
        self.loading_spinner = LoadingSpinner("טוען חבילות...")
        main_layout.addWidget(
            self.loading_spinner, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Packages container - responsive grid
        self.packages_container = QWidget()
        self.packages_container.setStyleSheet("background: transparent;")
        self.packages_layout = QGridLayout(self.packages_container)
        self.packages_layout.setHorizontalSpacing(Spacing.LG)
        self.packages_layout.setVerticalSpacing(Spacing.LG)
        self.packages_layout.setContentsMargins(
            Spacing.SM, Spacing.SM, Spacing.SM, Spacing.XXL
        )
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Scroll area - with room for shadows
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.packages_container)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Important: Don't clip shadows
        self.scroll.viewport().setStyleSheet("background: transparent;")
        self.scroll.setStyleSheet(
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
        """
        )

        main_layout.addSpacing(Spacing.SM)
        main_layout.addWidget(self.scroll, 1)

    def resizeEvent(self, event):
        """Reflow cards on resize for responsive grid"""
        super().resizeEvent(event)
        if self.package_cards:
            self._reflow_timer.start(120)

    def load_packages(self):
        """Load packages from Firebase"""
        QTimer.singleShot(300, self._fetch_packages)

    def _fetch_packages(self):
        """Fetch packages from service"""
        logger.debug("PackagesPage._fetch_packages called")
        # Safety check: widget may be deleted during test teardown
        try:
            spinner_valid = self.loading_spinner is not None
        except RuntimeError:
            spinner_valid = False
        try:
            result = self.package_service.get_all_packages()
        except Exception as e:
            logger.error(f"Failed to fetch packages: {e}")
            if spinner_valid:
                try:
                    self.loading_spinner.hide()
                except RuntimeError:
                    spinner_valid = False
            self._show_error()
            return

        logger.debug(f"Package fetch result: success={result.get('success')}")

        if not result.get("success"):
            logger.error(f"Failed to fetch packages: {result.get('error')}")
            if spinner_valid:
                try:
                    self.loading_spinner.hide()
                except RuntimeError:
                    spinner_valid = False
            self._show_error()
            return

        self.packages = result.get("data", [])
        logger.info(f"PackagesPage: Received {len(self.packages)} packages to display")
        if spinner_valid:
            try:
                self.loading_spinner.hide()
            except RuntimeError:
                spinner_valid = False

        if not self.packages:
            logger.warning("No packages to display - showing empty state")
            self._show_empty()
            return

        logger.debug(f"Displaying {len(self.packages)} packages")
        self._display_packages()

    def _show_error(self):
        """Show error state"""
        self._show_state(EmptyState("■", "שגיאה בטעינה", "לא הצלחנו לטעון את החבילות"))

    def _show_empty(self):
        """Show empty state"""
        self._show_state(EmptyState("■", "אין חבילות זמינות", "נסה שוב מאוחר יותר"))

    def _show_state(self, widget: QWidget):
        """Show a single centered state widget"""
        self._clear_grid(delete_widgets=True)
        self._state_widget = widget
        self._layout_packages()

    def _clear_grid(self, delete_widgets: bool = True):
        """Clear the packages grid"""
        while self.packages_layout.count():
            item = self.packages_layout.takeAt(0)
            widget = item.widget()
            if widget and delete_widgets:
                widget.setParent(None)

    def _display_packages(self):
        """Display packages in a responsive grid"""
        self._clear_grid(delete_widgets=True)
        self._state_widget = None
        self.package_cards = []
        self._featured_package_id = self._select_featured_package_id()
        for package in self.packages:
            if isinstance(package, dict) and "name" in package:
                card = self._create_package_card(
                    package, is_featured=self._is_featured(package)
                )
                self.package_cards.append(card)

        self._layout_packages()

    def _layout_packages(self):
        """Lay out cards based on available width"""
        self._clear_grid(delete_widgets=False)
        if self._state_widget:
            columns = self._calculate_columns()
            self.packages_layout.addWidget(
                self._state_widget, 0, 0, 1, columns, Qt.AlignmentFlag.AlignCenter
            )
            return

        if not self.package_cards:
            return

        columns = self._calculate_columns()
        row = 0
        col = 0
        for card in self.package_cards:
            self.packages_layout.addWidget(card, row, col)
            col += 1
            if col >= columns:
                col = 0
                row += 1

        for i in range(columns):
            self.packages_layout.setColumnStretch(i, 1)

    def _calculate_columns(self) -> int:
        """Determine number of columns based on available width"""
        available_width = max(1, self.scroll.viewport().width() - Spacing.LG)
        card_min_width = 280
        max_columns = max(1, available_width // (card_min_width + Spacing.LG))
        return min(max_columns, max(1, len(self.package_cards)))

    def _create_package_card(self, package: Dict, is_featured: bool = False) -> QFrame:
        """Create a modern package card"""
        card = QFrame()
        card.setMinimumWidth(260)
        card.setMinimumHeight(320)
        card.setMaximumHeight(420)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        card.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.WHITE},
                    stop:1 {Colors.GRAY_50}
                );
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
        layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        layout.setSpacing(Spacing.XS)

        if is_featured:
            badge = QLabel("מומלץ")
            badge.setFont(
                QFont(
                    Typography.FONT_FAMILY, Typography.SIZE_SM, Typography.WEIGHT_BOLD
                )
            )
            badge.setStyleSheet(
                f"""
                color: {Colors.WHITE};
                background: {Gradients.PRIMARY};
                padding: {Spacing.XS}px {Spacing.MD}px;
                border-radius: {BorderRadius.FULL}px;
            """
            )
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)

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
        desc.setMaximumHeight(28)
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
        features_layout.setSpacing(Spacing.XS)

        # Time - only show if package includes time
        minutes = package.get("minutes", 0)
        if minutes > 0:
            hours = minutes // 60
            mins = minutes % 60
            time_text = f"●  {hours}:{mins:02d} שעות"
            time_lbl = self._create_feature_label(time_text, Colors.PRIMARY)
            features_layout.addWidget(time_lbl)

        # Prints - only show if package includes print balance
        prints = package.get("prints", 0)
        if prints > 0:
            prints_text = f"●  {prints}₪ יתרת הדפסות"
            prints_lbl = self._create_feature_label(prints_text, Colors.ACCENT)
            features_layout.addWidget(prints_lbl)

        validity_text = self._get_validity_text(package)
        if validity_text:
            validity_lbl = self._create_feature_label(validity_text, Colors.WARNING)
            features_layout.addWidget(validity_lbl)

        layout.addWidget(features)

        # Price (with discount if applicable)
        pricing = PackageService.calculate_final_price(package)
        final_price = pricing["final_price"]
        original_price = pricing["original_price"]
        discount_percent = pricing["discount_percent"]

        # Price container - give it minimum height to prevent cutoff
        price_container = QWidget()
        price_container.setMinimumHeight(54 if discount_percent > 0 else 40)
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
            background: {color}10;
            color: {color};
            padding: {Spacing.XS}px {Spacing.MD}px;
            border-radius: {BorderRadius.SM}px;
            border-right: 3px solid {color};
        """
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def _get_validity_text(self, package: Dict) -> str:
        """Return validity display text for a package"""
        validity_days = package.get("validityDays", 0)
        if isinstance(validity_days, (int, float)) and validity_days > 0:
            return f"●  תוקף: {int(validity_days)} ימים"

        for key in ("validUntil", "expiresAt", "expiryDate"):
            date_str = package.get(key)
            if not date_str:
                continue
            try:
                dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
                return f"●  תוקף עד: {dt.strftime('%d/%m/%Y')}"
            except Exception:
                continue

        return ""

    def _select_featured_package_id(self) -> Optional[str]:
        """Select featured package based on highest discount"""
        best = None
        best_discount = 0
        for package in self.packages:
            pricing = PackageService.calculate_final_price(package)
            discount = pricing.get("discount_percent", 0)
            if discount > best_discount:
                best_discount = discount
                best = package
        if best:
            return best.get("id") or best.get("name")
        return None

    def _is_featured(self, package: Dict) -> bool:
        """Check if package should be highlighted"""
        if not self._featured_package_id:
            return False
        return self._featured_package_id in (
            package.get("id"),
            package.get("name"),
        )

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
