"""
Print Budget Service
Handles print budget validation, pricing, and deduction
"""

import traceback
from typing import Dict

from src.services.firebase_client import FirebaseClient
from src.utils.logger import get_logger


logger = get_logger(__name__)


class PrintBudgetService:
    """Service for managing print budgets and pricing"""

    def __init__(self, firebase_client: FirebaseClient):
        self.firebase = firebase_client

    def get_organization_print_pricing(self, org_id: str) -> Dict:
        """
        Get organization print pricing configuration

        Args:
            org_id: Organization ID

        Returns:
            Dict with success status and pricing data
        """
        try:
            # Get organization metadata which includes print pricing
            # Note: FirebaseClient already prefixes with organizations/{org_id}/
            result = self.firebase.db_get(f"metadata")

            if not result.get("success"):
                logger.error(
                    f"Failed to get organization metadata: {result.get('error')}"
                )
                return {
                    "success": False,
                    "error": f"Failed to get organization metadata: "
                    f"{result.get('error')}",
                }

            metadata = result.get("data", {})

            # Extract print pricing (with defaults)
            pricing = {
                "black_and_white_price": metadata.get(
                    "blackAndWhitePrice", 1.0
                ),  # Default 1 NIS
                "color_price": metadata.get("colorPrice", 3.0),  # Default 3 NIS
            }

            return {"success": True, "pricing": pricing}

        except Exception as e:
            logger.error(f"Error getting organization print pricing: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Error getting organization print pricing: {str(e)}",
            }

    def set_organization_print_pricing(
        self, org_id: str, black_white_price: float, color_price: float
    ) -> Dict:
        """
        Set organization print pricing configuration

        Args:
            org_id: Organization ID
            black_white_price: Price per black and white page (in NIS)
            color_price: Price per color page (in NIS)

        Returns:
            Dict with success status
        """
        try:
            # Update organization metadata with print pricing
            pricing_data = {
                "blackAndWhitePrice": black_white_price,
                "colorPrice": color_price,
            }

            result = self.firebase.db_update(
                f"metadata", pricing_data
            )

            if not result.get("success"):
                logger.error(f"Failed to update print pricing: {result.get('error')}")
                return {
                    "success": False,
                    "error": f"Failed to update print pricing: {result.get('error')}",
                }

            logger.info(
                f"Print pricing updated for org {org_id}: "
                f"B&W={black_white_price} NIS, Color={color_price} NIS"
            )
            return {"success": True}

        except Exception as e:
            logger.error(f"Error setting organization print pricing: {e}")
            return {
                "success": False,
                "error": f"Error setting organization print pricing: {str(e)}",
            }

    def get_user_print_budget(self, user_id: str) -> Dict:
        """
        Get user's current print budget (stored in remainingPrints field)

        Args:
            user_id: User ID

        Returns:
            Dict with success status and budget amount
        """
        try:
            # Note: FirebaseClient already prefixes with organizations/{org_id}/
            result = self.firebase.db_get(f"users/{user_id}")

            if not result.get("success"):
                logger.error(f"Failed to get user data: {result.get('error')}")
                return {
                    "success": False,
                    "error": f"Failed to get user data: {result.get('error')}",
                }

            user_data = result.get("data", {})
            budget = user_data.get(
                "remainingPrints", 0.0
            )  # Budget in NIS (renamed from count)

            return {"success": True, "budget": budget}

        except Exception as e:
            logger.error(f"Error getting user print budget: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Error getting user print budget: {str(e)}",
            }

    def calculate_print_cost(
        self, org_id: str, black_white_pages: int, color_pages: int
    ) -> Dict:
        """
        Calculate cost for a print job

        Args:
            org_id: Organization ID
            black_white_pages: Number of black and white pages
            color_pages: Number of color pages

        Returns:
            Dict with success status and cost breakdown
        """
        try:
            # Get organization pricing
            pricing_result = self.get_organization_print_pricing(org_id)
            if not pricing_result.get("success"):
                return pricing_result

            pricing = pricing_result["pricing"]

            # Calculate costs
            black_white_cost = black_white_pages * pricing["black_and_white_price"]
            color_cost = color_pages * pricing["color_price"]
            total_cost = black_white_cost + color_cost

            return {
                "success": True,
                "cost_breakdown": {
                    "black_white_pages": black_white_pages,
                    "color_pages": color_pages,
                    "black_white_cost": black_white_cost,
                    "color_cost": color_cost,
                    "total_cost": total_cost,
                },
            }

        except Exception as e:
            logger.error(f"Error calculating print cost: {e}")
            return {
                "success": False,
                "error": f"Error calculating print cost: {str(e)}",
            }

    def validate_print_budget(
        self, user_id: str, org_id: str, black_white_pages: int, color_pages: int
    ) -> Dict:
        """
        Validate if user has enough budget for print job

        Args:
            user_id: User ID
            org_id: Organization ID
            black_white_pages: Number of black and white pages
            color_pages: Number of color pages

        Returns:
            Dict with validation result and details
        """
        try:
            # Get user budget
            budget_result = self.get_user_print_budget(user_id)
            if not budget_result.get("success"):
                return budget_result

            # Calculate print cost
            cost_result = self.calculate_print_cost(
                org_id, black_white_pages, color_pages
            )
            if not cost_result.get("success"):
                return cost_result

            user_budget = budget_result["budget"]
            total_cost = cost_result["cost_breakdown"]["total_cost"]

            has_sufficient_budget = user_budget >= total_cost
            remaining_after_print = (
                user_budget - total_cost if has_sufficient_budget else user_budget
            )

            return {
                "success": True,
                "can_print": has_sufficient_budget,
                "user_budget": user_budget,
                "print_cost": total_cost,
                "remaining_after_print": remaining_after_print,
                "cost_breakdown": cost_result["cost_breakdown"],
                "insufficient_amount": (
                    total_cost - user_budget if not has_sufficient_budget else 0
                ),
            }

        except Exception as e:
            logger.error(f"Error validating print budget: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Error validating print budget: {str(e)}",
            }

    def deduct_print_budget(
        self, user_id: str, org_id: str, black_white_pages: int, color_pages: int
    ) -> Dict:
        """
        Deduct print cost from user's budget after successful printing

        Args:
            user_id: User ID
            org_id: Organization ID
            black_white_pages: Number of black and white pages printed
            color_pages: Number of color pages printed

        Returns:
            Dict with success status and updated budget
        """
        try:
            # First validate budget
            validation_result = self.validate_print_budget(
                user_id, org_id, black_white_pages, color_pages
            )
            if not validation_result.get("success"):
                return validation_result

            if not validation_result.get("can_print"):
                return {
                    "success": False,
                    "error": "Insufficient budget for print job",
                    "insufficient_amount": validation_result.get(
                        "insufficient_amount", 0
                    ),
                }

            # Get current budget
            budget_result = self.get_user_print_budget(user_id)
            if not budget_result.get("success"):
                return budget_result

            # Calculate new budget
            current_budget = budget_result["budget"]
            print_cost = validation_result["print_cost"]
            new_budget = current_budget - print_cost

            # Update user budget (stored in remainingPrints field)
            from datetime import datetime

            # Note: FirebaseClient already prefixes with organizations/{org_id}/
            result = self.firebase.db_update(
                f"users/{user_id}",
                {
                    "remainingPrints": new_budget,
                    "updatedAt": datetime.now().isoformat(),
                    "lastPrintDeduction": datetime.now().isoformat(),
                },
            )

            if not result.get("success"):
                logger.error(
                    f"Failed to update user print budget: {result.get('error')}"
                )
                return {
                    "success": False,
                    "error": f"Failed to update user print budget: "
                    f"{result.get('error')}",
                }

            logger.info(
                f"Print budget deducted for user {user_id}: "
                f"{print_cost} NIS, remaining: {new_budget} NIS"
            )

            return {
                "success": True,
                "previous_budget": current_budget,
                "deducted_amount": print_cost,
                "new_budget": new_budget,
                "cost_breakdown": validation_result["cost_breakdown"],
            }

        except Exception as e:
            logger.error(f"Error deducting print budget: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"Error deducting print budget: {str(e)}",
            }

    def add_print_budget(
        self, user_id: str, amount: float, reason: str = "purchase"
    ) -> Dict:
        """
        Add budget to user's print account (e.g., after package purchase)

        Args:
            user_id: User ID
            amount: Amount to add in NIS
            reason: Reason for adding budget (e.g., "purchase", "refund")

        Returns:
            Dict with success status and updated budget
        """
        try:
            # Get current budget
            budget_result = self.get_user_print_budget(user_id)
            if not budget_result.get("success"):
                return budget_result

            current_budget = budget_result["budget"]
            new_budget = current_budget + amount

            # Update user budget (stored in remainingPrints field)
            from datetime import datetime

            # Note: FirebaseClient already prefixes with organizations/{org_id}/
            result = self.firebase.db_update(
                f"users/{user_id}",
                {
                    "remainingPrints": new_budget,
                    "updatedAt": datetime.now().isoformat(),
                    "lastBudgetAddition": datetime.now().isoformat(),
                    "lastBudgetAdditionReason": reason,
                },
            )

            if not result.get("success"):
                logger.error(f"Failed to add print budget: {result.get('error')}")
                return {
                    "success": False,
                    "error": f"Failed to add print budget: " f"{result.get('error')}",
                }

            logger.info(
                f"Print budget added for user {user_id}: "
                f"+{amount} NIS, new total: {new_budget} NIS"
            )

            return {
                "success": True,
                "previous_budget": current_budget,
                "added_amount": amount,
                "new_budget": new_budget,
                "reason": reason,
            }

        except Exception as e:
            logger.error(f"Error adding print budget: {e}")
            return {"success": False, "error": f"Error adding print budget: {str(e)}"}
