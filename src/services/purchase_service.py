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

    def get_user_purchase_history(self, user_id: str) -> Dict:
        """
        Get all purchases for a specific user
        
        Returns:
            {'success': bool, 'purchases': list, 'error': str}
        """
        logger.info(f"Fetching purchase history for user {user_id}")
        
        # Check authentication
        if not self.firebase.id_token:
            logger.error("Firebase client not authenticated")
            return {
                'success': False,
                'error': 'Not authenticated'
            }
        
        try:
            # Get all purchases for the organization
            result = self.firebase.db_get('purchases')
            
            if not result.get('success'):
                logger.error(f"Failed to fetch purchases: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'Failed to fetch purchases')
                }
            
            purchases_data = result.get('data', {})
            if not purchases_data:
                return {
                    'success': True,
                    'purchases': []
                }
            
            # Filter purchases for the specific user
            user_purchases = []
            for purchase_id, purchase_data in purchases_data.items():
                if purchase_data.get('userId') == user_id:
                    # Add the purchase ID to the data
                    purchase_data['id'] = purchase_id
                    user_purchases.append(purchase_data)
            
            # Sort by creation date (newest first)
            user_purchases.sort(
                key=lambda x: x.get('createdAt', ''), 
                reverse=True
            )
            
            logger.info(f"Found {len(user_purchases)} purchases for user {user_id}")
            
            return {
                'success': True,
                'purchases': user_purchases
            }
            
        except Exception as e:
            logger.exception("Failed to fetch user purchase history")
            return {
                'success': False,
                'error': str(e)
            }

    def get_purchase_statistics(self, user_id: str) -> Dict:
        """
        Get purchase statistics for a user
        
        Returns:
            {'success': bool, 'stats': dict, 'error': str}
        """
        logger.info(f"Calculating purchase statistics for user {user_id}")
        
        try:
            # Get user purchases
            history_result = self.get_user_purchase_history(user_id)
            
            if not history_result.get('success'):
                return {
                    'success': False,
                    'error': history_result.get('error', 'Failed to fetch purchases')
                }
            
            purchases = history_result.get('purchases', [])
            
            # Calculate statistics
            total_spent = sum(
                self._safe_int(p.get('amount', 0)) for p in purchases 
                if p.get('status') == 'completed'
            )
            
            completed_purchases = len([
                p for p in purchases 
                if p.get('status') == 'completed'
            ])
            
            pending_purchases = len([
                p for p in purchases 
                if p.get('status') == 'pending'
            ])
            
            failed_purchases = len([
                p for p in purchases 
                if p.get('status') == 'failed'
            ])
            
            total_purchases = len(purchases)
            
            stats = {
                'total_spent': total_spent,
                'completed_purchases': completed_purchases,
                'pending_purchases': pending_purchases,
                'failed_purchases': failed_purchases,
                'total_purchases': total_purchases
            }
            
            logger.info(f"Purchase stats calculated: {stats}")
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            logger.exception("Failed to calculate purchase statistics")
            return {
                'success': False,
                'error': str(e)
            }

    def _safe_int(self, value, default=0):
        """Safely convert value to integer, handling strings and None"""
        if value is None:
            return default
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return default