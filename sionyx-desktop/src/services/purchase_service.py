"""
Purchase Service
Handle package purchases with pending state
Refactored to use base service for consistency
"""

from datetime import datetime
from typing import Dict

import requests

from services.base_service import DatabaseService
from services.firebase_client import FirebaseClient
from utils.logger import get_logger


logger = get_logger(__name__)


class PurchaseService(DatabaseService):
    """Manage package purchases with callback verification"""

    def __init__(self, firebase_client: FirebaseClient):
        super().__init__(firebase_client)
        # MULTI-TENANCY: Get org_id for direct requests
        self.org_id = firebase_client.org_id

    def get_collection_name(self) -> str:
        """Return the collection name for purchases"""
        return "purchases"

    def create_pending_purchase(self, user_id: str, package: Dict) -> Dict:
        """
        Create pending purchase record BEFORE payment

        Returns:
            {'success': bool, 'purchase_id': str, 'error': str}
        """
        logger.info(f"Creating pending purchase for user {user_id}")

        try:
            purchase_data = {
                "userId": user_id,
                "packageId": package.get("id"),
                "packageName": package.get("name"),
                "minutes": package.get("minutes"),
                "prints": package.get("prints"),
                "printBudget": package.get("prints"),  # For consistency with callback
                "validityDays": package.get("validityDays", 0),  # Package expiration
                "amount": package.get("price"),  # Will update with final amount
                "status": "pending",
                "createdAt": datetime.now().isoformat(),
                "updatedAt": datetime.now().isoformat(),
            }

            # Create in Firebase with multi-tenancy support
            org_path = f"organizations/{self.org_id}/purchases"
            response = requests.post(
                f"{self.firebase.database_url}/{org_path}.json",
                params={"auth": self.firebase.id_token},
                json=purchase_data,
                timeout=30,
            )

            if response.status_code != 200:
                logger.error(f"Failed to create pending purchase: {response.text}")
                return {"success": False, "error": "Failed to create purchase record"}

            purchase_id = response.json()["name"]
            logger.info(f"Pending purchase created: {purchase_id}")

            return {"success": True, "purchase_id": purchase_id}

        except Exception as e:
            logger.exception("Failed to create pending purchase")
            return {"success": False, "error": str(e)}

    def listen_for_purchase_completion(self, purchase_id: str, timeout: int = 300):
        """
        Listen for purchase completion (called from desktop app)
        This would be replaced with Firebase real-time listener

        Args:
            purchase_id: Purchase ID to monitor
            timeout: Maximum seconds to wait
        """
        # This will be handled by Firebase real-time listener in payment dialog

    def get_purchase_status(self, purchase_id: str) -> Dict:
        """Get current purchase status"""
        result = self.firebase.db_get(f"purchases/{purchase_id}")

        if result.get("success"):
            return {"success": True, "purchase": result.get("data")}

        return {"success": False, "error": "Purchase not found"}

    def get_user_purchase_history(self, user_id: str) -> Dict:
        """
        Get all purchases for a specific user using base service

        Returns:
            {'success': bool, 'purchases': list, 'error': str}
        """
        self.log_operation("get_user_purchase_history", f"User ID: {user_id}")

        # Use base service to get all purchases
        result = self.get_all_documents()

        if not result.get("success"):
            return result

        all_purchases = result.get("data", [])

        # Filter purchases for the specific user
        user_purchases = [
            purchase for purchase in all_purchases if purchase.get("userId") == user_id
        ]

        # Sort by creation date (newest first)
        user_purchases.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

        self.log_operation(
            "get_user_purchase_history",
            f"Found {len(user_purchases)} purchases for user {user_id}",
        )

        return self.create_success_response(
            user_purchases, f"Found {len(user_purchases)} purchases"
        )

    def get_purchase_statistics(self, user_id: str) -> Dict:
        """
        Get purchase statistics for a user using base service

        Returns:
            {'success': bool, 'stats': dict, 'error': str}
        """
        self.log_operation("get_purchase_statistics", f"User ID: {user_id}")

        try:
            # Get user purchases using base service
            history_result = self.get_user_purchase_history(user_id)

            if not history_result.get("success"):
                return history_result

            purchases = history_result.get("data", [])

            # Calculate statistics using base service methods
            total_spent = sum(
                self.safe_int(p.get("amount", 0))
                for p in purchases
                if p.get("status") == "completed"
            )

            completed_purchases = len(
                [p for p in purchases if p.get("status") == "completed"]
            )

            pending_purchases = len(
                [p for p in purchases if p.get("status") == "pending"]
            )

            failed_purchases = len(
                [p for p in purchases if p.get("status") == "failed"]
            )

            total_purchases = len(purchases)

            stats = {
                "total_spent": total_spent,
                "completed_purchases": completed_purchases,
                "pending_purchases": pending_purchases,
                "failed_purchases": failed_purchases,
                "total_purchases": total_purchases,
            }

            self.log_operation("get_purchase_statistics", f"Stats calculated: {stats}")

            return self.create_success_response(
                stats, f"Statistics calculated for {total_purchases} purchases"
            )

        except Exception as e:
            return self.handle_firebase_error(
                e, f"calculate purchase statistics for user {user_id}"
            )
