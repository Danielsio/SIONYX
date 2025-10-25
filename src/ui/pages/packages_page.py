"""
Packages Page
Browse and purchase time/print packages
Refactored to use centralized constants and base components
"""

from typing import Dict

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from services.package_service import PackageService
from ui.components.base_components import (
    ActionButton,
    BaseCard,
    LoadingSpinner,
)
from ui.constants.ui_constants import (
    BorderRadius,
    Colors,
    Dimensions,
    Shadows,
    Spacing,
    Typography,
    UIStrings,
    get_shadow_effect,
)
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
        """Initialize modern UI using base components and constants"""
        # Set RTL layout direction for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Set background using constants
        self.setStyleSheet(
            f"""
            QWidget {{
                background: {Colors.BG_PRIMARY};
            }}
        """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            Spacing.PAGE_MARGIN,
            Spacing.SECTION_MARGIN,
            Spacing.PAGE_MARGIN,
            Spacing.SECTION_MARGIN,
        )
        main_layout.setSpacing(Spacing.SECTION_SPACING)

        # Create header matching history page style
        self.create_header(main_layout)

        # Packages grid container using constants
        self.packages_container = QWidget()
        self.packages_container.setStyleSheet("background: transparent;")
        self.packages_layout = QGridLayout(self.packages_container)
        self.packages_layout.setSpacing(Spacing.CARD_SPACING)
        self.packages_layout.setContentsMargins(
            Spacing.CARD_MARGIN,
            Spacing.CARD_MARGIN,
            Spacing.CARD_MARGIN,
            Spacing.CARD_MARGIN,
        )
        self.packages_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logger.debug("Packages grid layout created", component="packages_page")

        # Scroll area using constants
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.packages_container)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setMinimumHeight(Dimensions.CONTENT_MIN_HEIGHT)
        scroll.setStyleSheet(
            f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {Colors.BORDER_LIGHT};
                width: {Dimensions.SCROLL_BAR_WIDTH}px;
                border-radius: {Dimensions.SCROLL_BAR_RADIUS}px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.TEXT_MUTED};
                border-radius: {Dimensions.SCROLL_BAR_RADIUS}px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Colors.TEXT_SECONDARY};
            }}
        """
        )

        # Loading state using base component
        self.loading_spinner = LoadingSpinner("טוען חבילות...")

        main_layout.addWidget(self.loading_spinner)
        main_layout.addWidget(scroll, 1)

        logger.debug("Packages page initialized", component="packages_page")

    def create_header(self, parent_layout):
        """Create page header matching history page style"""
        # Clean header section matching history page style
        header_container = QWidget()
        header_container.setStyleSheet(
            """
            QWidget {
                background: #3B82F6;
                border-radius: 20px;
                padding: 20px;
            }
        """
        )

        # Add shadow to header - Enhanced shadow effect
        header_shadow = QGraphicsDropShadowEffect()
        header_shadow.setBlurRadius(50)
        header_shadow.setXOffset(0)
        header_shadow.setYOffset(15)
        header_shadow.setColor(QColor(0, 0, 0, 65))
        header_container.setGraphicsEffect(header_shadow)
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(30, 25, 30, 25)
        header_layout.setSpacing(8)

        # Main title with stunning typography
        title = QLabel("חבילות זמינות")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: 800;
                margin-bottom: 8px;
            }
        """
        )

        # Subtitle with elegant styling
        subtitle = QLabel("רכוש זמן נוסף וקרדיטי הדפסה")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            """
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                font-weight: 400;
            }
        """
        )

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        parent_layout.addWidget(header_container)

    def load_packages(self):
        """Load packages from Firebase"""
        logger.debug("Loading packages from database", action="load_packages")

        # Simulate async load with QTimer
        QTimer.singleShot(500, self._fetch_packages)

    def _fetch_packages(self):
        """Fetch packages from service"""
        result = self.package_service.get_all_packages()

        if not result.get("success"):
            logger.error(
                "Failed to load packages",
                error=result.get("error"),
                action="load_packages",
            )
            self.show_error_state("❌ נכשל בטעינת החבילות")
            return

        self.packages = result.get("data", [])

        if len(self.packages) == 0:
            logger.warning("No packages available", action="load_packages")
            self.show_empty_state()
            return

        logger.info(
            "Packages loaded successfully",
            count=len(self.packages),
            action="load_packages",
        )

        # Hide loading spinner and show packages
        self.loading_spinner.hide()
        self.display_packages()

    def show_error_state(self, message: str):
        """Show error state with message"""
        self.loading_spinner.hide()
        # Could implement error state component here

    def show_empty_state(self):
        """Show empty state when no packages available"""
        self.loading_spinner.hide()
        # Could implement empty state component here

    def refresh_user_data(self):
        """Refresh user data and reload packages"""
        logger.debug("Refreshing user data", component="packages_page")

        # Get current user from auth service
        self.current_user = self.auth_service.get_current_user()

        # Don't reload packages here - they're already loaded during initialization
        # This prevents duplicate package loading

    def clear_user_data(self):
        """Clear all user data (called on logout)"""
        logger.debug("Clearing user data", component="packages_page")

        self.current_user = None
        self.packages = []

        # Show empty state
        self.state_label.setText("📦 אין חבילות זמינות")
        self.state_label.show()

    def display_packages(self):
        """Display packages in beautiful responsive grid"""
        logger.debug(
            "Displaying packages", count=len(self.packages), action="display_packages"
        )

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
            if isinstance(package, dict) and "name" in package:
                valid_packages.append(package)

        if len(valid_packages) == 0:
            logger.warning("No valid packages to display", action="display_packages")
            return

        for package in valid_packages:
            card = self.create_package_card(package)

            # Add card to grid with proper alignment
            self.packages_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignCenter)

            col += 1
            if col >= max_columns:
                col = 0
                row += 1

        # Force UI refresh and repaint
        self.packages_container.update()
        self.packages_container.repaint()
        self.update()
        self.repaint()

    def create_package_card(self, package: Dict) -> QFrame:
        """Create package card using base components and constants"""
        # Validate package data
        if not isinstance(package, dict):
            logger.error(
                "Invalid package data",
                package_type=type(package).__name__,
                action="create_card",
            )
            return QFrame()  # Return empty frame for invalid data

        # Create base card with package-specific styling
        card = BaseCard("package")
        card.setFixedSize(Dimensions.PACKAGE_CARD_WIDTH, Dimensions.PACKAGE_CARD_HEIGHT)
        card.setStyleSheet(
            f"""
            QFrame {{
                background: {Colors.WHITE};
                border-radius: {BorderRadius.EXTRA_LARGE}px;
                border: 2px solid {Colors.BORDER_LIGHT};
            }}
            QFrame:hover {{
                border: 2px solid {Colors.PRIMARY};
                background: {Colors.GRAY_50};
            }}
        """
        )

        # Apply shadow using constants
        shadow_config = get_shadow_effect(Shadows.LARGE_BLUR, Shadows.Y_OFFSET_LARGE)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(shadow_config["blur_radius"])
        shadow.setXOffset(shadow_config["x_offset"])
        shadow.setYOffset(shadow_config["y_offset"])
        shadow.setColor(QColor(shadow_config["color"]))
        card.setGraphicsEffect(shadow)

        # Main layout using constants
        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
        )
        layout.setSpacing(Spacing.COMPONENT_MARGIN)

        # Package name using constants
        name = QLabel(package.get("name", "חבילה"))
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)
        name.setStyleSheet(
            f"""
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.SIZE_2XL}px;
                font-weight: {Typography.WEIGHT_BOLD};
                line-height: {Typography.LINE_HEIGHT_TIGHT};
                margin-bottom: {Spacing.TIGHT_SPACING}px;
            }}
        """
        )

        # Description using constants
        desc = QLabel(package.get("description", "תיאור החבילה"))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Typography.SIZE_MD}px;
                font-weight: {Typography.WEIGHT_NORMAL};
                line-height: {Typography.LINE_HEIGHT_NORMAL};
                margin-bottom: {Spacing.COMPONENT_MARGIN}px;
            }}
        """
        )

        # Elegant separator using constants
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(
            f"""
            QFrame {{
                color: {Colors.BORDER_LIGHT};
                background-color: {Colors.BORDER_LIGHT};
                border: none;
                height: 1px;
                margin: {Spacing.TIGHT_SPACING}px 0;
            }}
        """
        )

        # Features container using constants
        features_container = QWidget()
        features_layout = QVBoxLayout(features_container)
        features_layout.setContentsMargins(0, 0, 0, 0)
        features_layout.setSpacing(Spacing.ELEMENT_SPACING)

        # Time feature using constants
        time_minutes = package.get("minutes", 0)
        hours = time_minutes // 60
        mins = time_minutes % 60
        time_text = (
            f"⏰ {hours}:{mins:02d} שעות" if time_minutes > 0 else "⏰ ללא הגבלת זמן"
        )
        time_label = QLabel(time_text)
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {Colors.BG_PRIMARY};
                color: {Colors.GRAY_600};
                font-size: {Typography.SIZE_MD}px;
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                padding: {Spacing.ELEMENT_SPACING}px {Spacing.COMPONENT_MARGIN}px;
                border-radius: {BorderRadius.MEDIUM}px;
                border-left: 4px solid {Colors.PRIMARY};
            }}
        """
        )

        # Prints feature using constants - now shows budget in NIS
        prints = package.get("prints", 0)
        prints_text = f"🖨️ {prints}₪ יתרת הדפסות" if prints > 0 else "🖨️ ללא הגבלת הדפסות"
        prints_label = QLabel(prints_text)
        prints_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prints_label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {Colors.SUCCESS_LIGHT};
                color: {Colors.SUCCESS_HOVER};
                font-size: {Typography.SIZE_MD}px;
                font-weight: {Typography.WEIGHT_SEMIBOLD};
                padding: {Spacing.ELEMENT_SPACING}px {Spacing.COMPONENT_MARGIN}px;
                border-radius: {BorderRadius.MEDIUM}px;
                border-left: 4px solid {Colors.SUCCESS};
            }}
        """
        )

        features_layout.addWidget(time_label)
        features_layout.addWidget(prints_label)

        # Price section using constants
        price_container = QWidget()
        price_layout = QVBoxLayout(price_container)
        price_layout.setContentsMargins(0, Spacing.CARD_MARGIN, 0, Spacing.CARD_MARGIN)
        price_layout.setSpacing(Spacing.TIGHT_SPACING)

        # Price display using constants
        price = package.get("price", 0)
        price_label = QLabel(f"₪{price}")
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setStyleSheet(
            f"""
            QLabel {{
                color: {Colors.PRIMARY};
                font-size: {Typography.SIZE_3XL}px;
                font-weight: {Typography.WEIGHT_EXTRABOLD};
            }}
        """
        )
        price_layout.addWidget(price_label)

        # Purchase button using base component
        purchase_btn = ActionButton(UIStrings.BUY_NOW, "primary", "medium")
        purchase_btn.clicked.connect(lambda: self.handle_purchase(package))

        # Assemble the card
        layout.addWidget(name)
        layout.addWidget(desc)
        layout.addWidget(separator)
        layout.addWidget(features_container)
        layout.addStretch()  # Push price and button to bottom
        layout.addWidget(price_container)
        layout.addWidget(purchase_btn)

        return card

    def handle_purchase(self, package: Dict):
        """Handle package purchase"""
        logger.info(
            "Purchase initiated",
            package_name=package.get("name"),
            action="purchase_initiated",
        )

        from PyQt6.QtWidgets import QMessageBox

        from ui.payment_dialog import PaymentDialog

        # Open payment dialog (derive user and auth from parent)
        dialog = PaymentDialog(package, self)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # Payment successful
            payment_response = dialog.get_payment_response()

            if not payment_response:
                # Get parent window to show dialog
                parent_window = self.window()
                if hasattr(parent_window, "show_error"):
                    parent_window.show_error("שגיאת תשלום", "לא התקבל אישור תשלום")
                else:
                    QMessageBox.critical(self, "שגיאה", "לא התקבל אישור תשלום")
                return

            # Payment was successful - the purchase is already recorded by the Cloud Function
            # The user's account has been credited automatically
            logger.info("Payment completed successfully", action="payment_success")

            # Show success message
            parent_window = self.window()
            if hasattr(parent_window, "show_success"):
                parent_window.show_success(
                    "הרכישה הושלמה! 🎉",
                    "הרכישה שלך בוצעה בהצלחה!",
                    f"נוסף לחשבונך:<br>"
                    f"• <b>{package.get('minutes')} דקות</b> של זמן הפעלה<br>"
                    f"• <b>{package.get('prints')}₪</b> יתרת הדפסות",
                )
            else:
                QMessageBox.information(
                    self,
                    "רכישה הושלמה",
                    f"הרכישה בוצעה בהצלחה!\n\n"
                    f"נוספו לחשבונך:\n"
                    f"• {package.get('minutes')} דקות\n"
                    f"• {package.get('prints')}₪ יתרת הדפסות",
                )

            # Refresh packages page
            self.load_packages()
        else:
            # Payment cancelled
            logger.info("Payment cancelled by user", action="payment_cancelled")
