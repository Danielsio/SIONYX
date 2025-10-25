"""
Print Validation Service
Handles print job validation and budget checking during sessions
"""

from typing import Dict

from PyQt6.QtCore import QObject, pyqtSignal

from services.firebase_client import FirebaseClient
from services.print_budget_service import PrintBudgetService
from utils.logger import get_logger


logger = get_logger(__name__)


class PrintValidationService(QObject):
    """Service for validating print jobs and managing print budgets during sessions"""

    # Signals
    print_budget_insufficient = pyqtSignal(
        float, float
    )  # current_budget, required_amount
    print_budget_updated = pyqtSignal(float)  # new_budget_amount
    print_job_validated = pyqtSignal(bool, str)  # is_valid, message

    def __init__(self, firebase_client: FirebaseClient, user_id: str, org_id: str):
        super().__init__()
        self.firebase = firebase_client
        self.user_id = user_id
        self.org_id = org_id
        self.print_budget_service = PrintBudgetService(firebase_client)

    def validate_print_job(self, black_white_pages: int, color_pages: int) -> Dict:
        """
        Validate if user can perform a print job

        Args:
            black_white_pages: Number of black and white pages
            color_pages: Number of color pages

        Returns:
            Dict with validation result
        """
        try:
            logger.info(
                f"Validating print job: {black_white_pages} B&W, {color_pages} color pages"
            )

            # Validate budget
            validation_result = self.print_budget_service.validate_print_budget(
                self.user_id, self.org_id, black_white_pages, color_pages
            )

            if not validation_result.get("success"):
                logger.error(
                    f"Print budget validation failed: {validation_result.get('error')}"
                )
                return validation_result

            can_print = validation_result.get("can_print", False)
            user_budget = validation_result.get("user_budget", 0)
            print_cost = validation_result.get("print_cost", 0)

            if not can_print:
                insufficient_amount = validation_result.get("insufficient_amount", 0)
                logger.warning(
                    f"Insufficient print budget: {user_budget} NIS, need {print_cost} NIS"
                )

                # Emit signal for UI to show insufficient budget message
                self.print_budget_insufficient.emit(user_budget, print_cost)

                return {
                    "success": True,
                    "can_print": False,
                    "reason": "insufficient_budget",
                    "user_budget": user_budget,
                    "print_cost": print_cost,
                    "insufficient_amount": insufficient_amount,
                    "message": f"יתרת הדפסות לא מספקת. נדרש {print_cost}₪, יש לך {user_budget}₪",
                }

            logger.info(f"Print job validated successfully: {print_cost} NIS")
            self.print_job_validated.emit(True, f"הדפסה מאושרת: {print_cost}₪")

            return {
                "success": True,
                "can_print": True,
                "user_budget": user_budget,
                "print_cost": print_cost,
                "remaining_after_print": validation_result.get(
                    "remaining_after_print", 0
                ),
                "cost_breakdown": validation_result.get("cost_breakdown", {}),
                "message": f"הדפסה מאושרת: {print_cost}₪",
            }

        except Exception as e:
            logger.error(f"Error validating print job: {e}")
            return {"success": False, "error": f"Error validating print job: {str(e)}"}

    def process_successful_print(
        self, black_white_pages: int, color_pages: int
    ) -> Dict:
        """
        Process a successful print job and deduct budget

        Args:
            black_white_pages: Number of black and white pages printed
            color_pages: Number of color pages printed

        Returns:
            Dict with processing result
        """
        try:
            logger.info(
                f"Processing successful print: {black_white_pages} B&W, {color_pages} color pages"
            )

            # Deduct budget
            deduction_result = self.print_budget_service.deduct_print_budget(
                self.user_id, self.org_id, black_white_pages, color_pages
            )

            if not deduction_result.get("success"):
                logger.error(
                    f"Failed to deduct print budget: {deduction_result.get('error')}"
                )
                return deduction_result

            new_budget = deduction_result.get("new_budget", 0)
            deducted_amount = deduction_result.get("deducted_amount", 0)

            logger.info(
                f"Print budget deducted: {deducted_amount} NIS, remaining: {new_budget} NIS"
            )

            # Emit signal for UI to update budget display
            self.print_budget_updated.emit(new_budget)

            return {
                "success": True,
                "new_budget": new_budget,
                "deducted_amount": deducted_amount,
                "cost_breakdown": deduction_result.get("cost_breakdown", {}),
                "message": f"הדפסה הושלמה בהצלחה. נוכו {deducted_amount}₪",
            }

        except Exception as e:
            logger.error(f"Error processing successful print: {e}")
            return {
                "success": False,
                "error": f"Error processing successful print: {str(e)}",
            }

    def get_current_budget(self) -> Dict:
        """
        Get user's current print budget

        Returns:
            Dict with budget information
        """
        try:
            return self.print_budget_service.get_user_print_budget(self.user_id)
        except Exception as e:
            logger.error(f"Error getting current budget: {e}")
            return {
                "success": False,
                "error": f"Error getting current budget: {str(e)}",
            }

    def get_print_pricing(self) -> Dict:
        """
        Get organization print pricing

        Returns:
            Dict with pricing information
        """
        try:
            return self.print_budget_service.get_organization_print_pricing(self.org_id)
        except Exception as e:
            logger.error(f"Error getting print pricing: {e}")
            return {"success": False, "error": f"Error getting print pricing: {str(e)}"}

    def simulate_print_cost(self, black_white_pages: int, color_pages: int) -> Dict:
        """
        Simulate print cost without deducting budget

        Args:
            black_white_pages: Number of black and white pages
            color_pages: Number of color pages

        Returns:
            Dict with cost simulation
        """
        try:
            return self.print_budget_service.calculate_print_cost(
                self.org_id, black_white_pages, color_pages
            )
        except Exception as e:
            logger.error(f"Error simulating print cost: {e}")
            return {"success": False, "error": f"Error simulating print cost: {str(e)}"}
