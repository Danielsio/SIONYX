"""
Purchase Service
Handle package purchases with pending state
"""

from typing import Dict
from datetime import datetime
from services.firebase_client import FirebaseClient
from utils.logger import get_logger
import requests

logger = get_logger(__name__)


class PurchaseService:
    """Manage package purchases with callback verification"""

    def __init__(self, firebase_client: FirebaseClient):
        self.firebase = firebase_client
        # MULTI-TENANCY: Get org_id for direct requests
        self.org_id = firebase_client.org_id

    def create_pending_purchase(self, user_id: str, package: Dict) -> Dict:
        """
        Create pending purchase record BEFORE payment

        Returns:
            {'success': bool, 'purchase_id': str, 'error': str}
        """
        logger.info(f"Creating pending purchase for user {user_id}")

        try:
            purchase_data = {
                'userId': user_id,
                'packageId': package.get('id'),
                'packageName': package.get('name'),
                'minutes': package.get('minutes'),
                'prints': package.get('prints'),
                'amount': package.get('price'),  # Will update with final amount
                'status': 'pending',
                'createdAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat()
            }

            # Create in Firebase with multi-tenancy support
            org_path = f"organizations/{self.org_id}/purchases"
            response = requests.post(
                f"{self.firebase.database_url}/{org_path}.json",
                params={'auth': self.firebase.id_token},
                json=purchase_data
            )

            if response.status_code != 200:
                logger.error(f"Failed to create pending purchase: {response.text}")
                return {
                    'success': False,
                    'error': 'Failed to create purchase record'
                }

            purchase_id = response.json()['name']
            logger.info(f"Pending purchase created: {purchase_id}")

            return {
                'success': True,
                'purchase_id': purchase_id
            }

        except Exception as e:
            logger.exception("Failed to create pending purchase")
            return {
                'success': False,
                'error': str(e)
            }

    def listen_for_purchase_completion(self, purchase_id: str, timeout: int = 300):
        """
        Listen for purchase completion (called from desktop app)
        This would be replaced with Firebase real-time listener

        Args:
            purchase_id: Purchase ID to monitor
            timeout: Maximum seconds to wait
        """
        # This will be handled by Firebase real-time listener in payment dialog
        pass

    def get_purchase_status(self, purchase_id: str) -> Dict:
        """Get current purchase status"""
        result = self.firebase.db_get(f'purchases/{purchase_id}')

        if result.get('success'):
            return {
                'success': True,
                'purchase': result.get('data')
            }

        return {
            'success': False,
            'error': 'Purchase not found'
        }