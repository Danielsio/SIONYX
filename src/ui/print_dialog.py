"""
Print Dialog
Shows print job details and budget validation before printing
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
)

from src.services.print_validation_service import PrintValidationService
from ui.styles.base import Colors, Spacing
from src.utils.logger import get_logger


logger = get_logger(__name__)


class PrintDialog(QDialog):
    """Dialog for print job validation and budget checking"""

    print_approved = pyqtSignal(int, int)  # black_white_pages, color_pages
    print_cancelled = pyqtSignal()

    def __init__(self, print_validation_service: PrintValidationService, parent=None):
        super().__init__(parent)
        self.print_validation_service = print_validation_service
        self.black_white_pages = 0
        self.color_pages = 0
        self.validation_result = None

        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("אישור הדפסה")
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
        title_label = QLabel("אישור הדפסה")
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

        # Print details frame
        details_frame = QFrame()
        details_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 15px;
            }}
        """
        )
        details_layout = QVBoxLayout(details_frame)
        details_layout.setSpacing(8)

        # Print job details
        self.job_details_label = QLabel("פרטי ההדפסה:")
        self.job_details_label.setStyleSheet(
            f"font-weight: bold; color: {Colors.TEXT_PRIMARY};"
        )

        self.black_white_label = QLabel("דפים שחור-לבן: 0")
        self.color_label = QLabel("דפים צבעוניים: 0")
        self.total_cost_label = QLabel("עלות כוללת: 0₪")

        for label in [self.black_white_label, self.color_label, self.total_cost_label]:
            label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; margin-left: 10px;")

        details_layout.addWidget(self.job_details_label)
        details_layout.addWidget(self.black_white_label)
        details_layout.addWidget(self.color_label)
        details_layout.addWidget(self.total_cost_label)

        layout.addWidget(details_frame)

        # Budget info frame
        budget_frame = QFrame()
        budget_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 15px;
            }}
        """
        )
        budget_layout = QVBoxLayout(budget_frame)
        budget_layout.setSpacing(8)

        self.budget_label = QLabel("יתרת הדפסות:")
        self.budget_label.setStyleSheet(
            f"font-weight: bold; color: {Colors.TEXT_PRIMARY};"
        )

        self.current_budget_label = QLabel("יתרה נוכחית: 0₪")
        self.remaining_after_label = QLabel("יתרה לאחר הדפסה: 0₪")
        self.status_label = QLabel("")

        for label in [
            self.current_budget_label,
            self.remaining_after_label,
            self.status_label,
        ]:
            label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; margin-left: 10px;")

        budget_layout.addWidget(self.budget_label)
        budget_layout.addWidget(self.current_budget_label)
        budget_layout.addWidget(self.remaining_after_label)
        budget_layout.addWidget(self.status_label)

        layout.addWidget(budget_frame)

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
        self.cancel_button.clicked.connect(self.cancel_print)

        # Print button
        self.print_button = QPushButton("הדפס")
        self.print_button.setStyleSheet(
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
            QPushButton:disabled {{
                background-color: {Colors.BG_DISABLED};
                color: {Colors.TEXT_DISABLED};
            }}
        """
        )
        self.print_button.clicked.connect(self.approve_print)
        self.print_button.setEnabled(False)

        button_layout.addWidget(self.cancel_button)
        button_layout.addItem(
            QSpacerItem(20, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        )
        button_layout.addWidget(self.print_button)

        layout.addLayout(button_layout)

    def setup_connections(self):
        """Setup signal connections"""
        # Connect print validation service signals
        self.print_validation_service.print_budget_insufficient.connect(
            self.handle_insufficient_budget
        )
        self.print_validation_service.print_budget_updated.connect(
            self.update_budget_display
        )

    def set_print_job(self, black_white_pages: int, color_pages: int):
        """
        Set the print job details and validate budget

        Args:
            black_white_pages: Number of black and white pages
            color_pages: Number of color pages
        """
        self.black_white_pages = black_white_pages
        self.color_pages = color_pages

        # Update UI with print job details
        self.black_white_label.setText(f"דפים שחור-לבן: {black_white_pages}")
        self.color_label.setText(f"דפים צבעוניים: {color_pages}")

        # Validate print job
        self.validation_result = self.print_validation_service.validate_print_job(
            black_white_pages, color_pages
        )

        if self.validation_result.get("success"):
            self.update_validation_display()
        else:
            self.show_error_message(
                self.validation_result.get("error", "שגיאה לא ידועה")
            )

    def update_validation_display(self):
        """Update the display based on validation result"""
        if not self.validation_result:
            return

        can_print = self.validation_result.get("can_print", False)
        user_budget = self.validation_result.get("user_budget", 0)
        print_cost = self.validation_result.get("print_cost", 0)
        remaining_after = self.validation_result.get("remaining_after_print", 0)

        # Update budget display
        self.current_budget_label.setText(f"יתרה נוכחית: {user_budget:.2f}₪")
        self.total_cost_label.setText(f"עלות כוללת: {print_cost:.2f}₪")
        self.remaining_after_label.setText(f"יתרה לאחר הדפסה: {remaining_after:.2f}₪")

        # Update status and button
        if can_print:
            self.status_label.setText("✅ הדפסה מאושרת")
            self.status_label.setStyleSheet(
                f"color: {Colors.SUCCESS}; font-weight: bold; margin-left: 10px;"
            )
            self.print_button.setEnabled(True)
        else:
            self.status_label.setText("❌ יתרה לא מספקת")
            self.status_label.setStyleSheet(
                f"color: {Colors.ERROR}; font-weight: bold; margin-left: 10px;"
            )
            self.print_button.setEnabled(False)

    def handle_insufficient_budget(self, current_budget: float, required_amount: float):
        """Handle insufficient budget signal"""
        self.status_label.setText(f"❌ יתרה לא מספקת - נדרש {required_amount:.2f}₪")
        self.status_label.setStyleSheet(
            f"color: {Colors.ERROR}; font-weight: bold; margin-left: 10px;"
        )
        self.print_button.setEnabled(False)

    def update_budget_display(self, new_budget: float):
        """Update budget display when budget changes"""
        self.current_budget_label.setText(f"יתרה נוכחית: {new_budget:.2f}₪")

    def approve_print(self):
        """Approve the print job"""
        if not self.validation_result or not self.validation_result.get("can_print"):
            return

        logger.info(
            f"Print job approved: {self.black_white_pages} B&W, {self.color_pages} color"
        )
        self.print_approved.emit(self.black_white_pages, self.color_pages)
        self.accept()

    def cancel_print(self):
        """Cancel the print job"""
        logger.info("Print job cancelled by user")
        self.print_cancelled.emit()
        self.reject()

    def show_error_message(self, message: str):
        """Show error message"""
        self.status_label.setText(f"❌ {message}")
        self.status_label.setStyleSheet(
            f"color: {Colors.ERROR}; font-weight: bold; margin-left: 10px;"
        )
        self.print_button.setEnabled(False)
