"""
Print Pricing Dialog
Admin interface for setting organization print pricing
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from services.organization_metadata_service import OrganizationMetadataService
from ui.styles.base import Colors, Spacing
from utils.logger import get_logger


logger = get_logger(__name__)


class PrintPricingDialog(QDialog):
    """Dialog for setting organization print pricing"""

    pricing_updated = pyqtSignal(dict)  # pricing data

    def __init__(
        self,
        organization_metadata_service: OrganizationMetadataService,
        org_id: str,
        parent=None,
    ):
        super().__init__(parent)
        self.organization_metadata_service = organization_metadata_service
        self.org_id = org_id
        self.current_pricing = None

        self.init_ui()
        self.load_current_pricing()

    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("הגדרות מחירי הדפסה")
        self.setFixedSize(400, 300)
        self.setModal(True)

        # Set RTL layout direction for Hebrew support
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Spacing.PAGE_MARGIN,
            Spacing.SECTION_MARGIN,
            Spacing.PAGE_MARGIN,
            Spacing.SECTION_MARGIN,
        )
        layout.setSpacing(Spacing.SECTION_SPACING)

        # Title
        title_label = QLabel("הגדרות מחירי הדפסה")
        title_label.setStyleSheet(
            f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
                margin-bottom: 10px;
            }}
        """
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Pricing form frame
        form_frame = QFrame()
        form_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 15px;
            }}
        """
        )
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)

        # Black and white pricing
        bw_layout = QHBoxLayout()
        bw_label = QLabel("מחיר הדפסה שחור-לבן:")
        bw_label.setStyleSheet(
            f"font-weight: bold; color: {Colors.TEXT_PRIMARY}; min-width: 150px;"
        )

        self.bw_price_input = QLineEdit()
        self.bw_price_input.setPlaceholderText("1.0")
        self.bw_price_input.setStyleSheet(
            f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: {Colors.BG_PRIMARY};
                color: {Colors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {Colors.PRIMARY};
            }}
        """
        )

        nis_label = QLabel("₪")
        nis_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; min-width: 20px;")

        bw_layout.addWidget(nis_label)
        bw_layout.addWidget(self.bw_price_input)
        bw_layout.addWidget(bw_label)

        form_layout.addLayout(bw_layout)

        # Color pricing
        color_layout = QHBoxLayout()
        color_label = QLabel("מחיר הדפסה צבעונית:")
        color_label.setStyleSheet(
            f"font-weight: bold; color: {Colors.TEXT_PRIMARY}; min-width: 150px;"
        )

        self.color_price_input = QLineEdit()
        self.color_price_input.setPlaceholderText("3.0")
        self.color_price_input.setStyleSheet(
            f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: {Colors.BG_PRIMARY};
                color: {Colors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {Colors.PRIMARY};
            }}
        """
        )

        nis_label2 = QLabel("₪")
        nis_label2.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; min-width: 20px;")

        color_layout.addWidget(nis_label2)
        color_layout.addWidget(self.color_price_input)
        color_layout.addWidget(color_label)

        form_layout.addLayout(color_layout)

        # Note about currency (NIS is fixed)
        currency_note = QLabel("כל המחירים בשקלים (NIS)")
        currency_note.setStyleSheet(
            f"color: {Colors.TEXT_SECONDARY}; font-style: italic; margin-top: 10px;"
        )
        currency_note.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form_layout.addWidget(currency_note)

        layout.addWidget(form_frame)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.BUTTON_SPACING)

        # Cancel button
        self.cancel_button = QPushButton("ביטול")
        self.cancel_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {Colors.BG_SECONDARY};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
            }}
        """
        )
        self.cancel_button.clicked.connect(self.reject)

        # Save button
        self.save_button = QPushButton("שמור")
        self.save_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {Colors.SUCCESS};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #28a745;
            }}
        """
        )
        self.save_button.clicked.connect(self.save_pricing)

        button_layout.addWidget(self.cancel_button)
        button_layout.addItem(
            QSpacerItem(20, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

    def load_current_pricing(self):
        """Load current pricing from organization metadata"""
        try:
            result = self.organization_metadata_service.get_print_pricing(self.org_id)

            if result.get("success"):
                pricing = result["pricing"]
                self.current_pricing = pricing

                # Update UI with current values
                self.bw_price_input.setText(
                    str(pricing.get("black_and_white_price", 1.0))
                )
                self.color_price_input.setText(str(pricing.get("color_price", 3.0)))
            else:
                # Use defaults
                self.bw_price_input.setText("1.0")
                self.color_price_input.setText("3.0")

        except Exception as e:
            logger.error(f"Error loading current pricing: {e}")
            # Use defaults
            self.bw_price_input.setText("1.0")
            self.color_price_input.setText("3.0")

    def save_pricing(self):
        """Save the pricing configuration"""
        try:
            # Validate inputs
            try:
                bw_price = float(self.bw_price_input.text())
                color_price = float(self.color_price_input.text())
            except ValueError:
                QMessageBox.warning(self, "שגיאה", "נא להזין מחירים תקינים")
                return

            if bw_price <= 0 or color_price <= 0:
                QMessageBox.warning(self, "שגיאה", "המחירים חייבים להיות גדולים מ-0")
                return

            # Save pricing (currency is always NIS)
            result = self.organization_metadata_service.set_print_pricing(
                self.org_id, bw_price, color_price
            )

            if result.get("success"):
                QMessageBox.information(self, "הצלחה", "מחירי ההדפסה נשמרו בהצלחה")

                # Emit signal with new pricing
                new_pricing = {
                    "black_and_white_price": bw_price,
                    "color_price": color_price,
                }
                self.pricing_updated.emit(new_pricing)

                self.accept()
            else:
                QMessageBox.critical(
                    self, "שגיאה", f"נכשל לשמור מחירי הדפסה: {result.get('error')}"
                )

        except Exception as e:
            logger.error(f"Error saving pricing: {e}")
            QMessageBox.critical(self, "שגיאה", f"שגיאה בשמירת מחירי הדפסה: {str(e)}")
