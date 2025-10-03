"""
Purchase Service
Handle package purchases and user credit updates
"""

from typing import Dict
from datetime import datetime
from services.firebase_client import FirebaseClient
from utils.logger import get_logger

logger = get_logger(__name__)


class PurchaseService:
    """Manage package purchases"""

    def __init__(self, firebase_client: FirebaseClient):
        self.firebase = firebase_client

    def record_purchase(self, user_id: str, package: Dict, payment_response: Dict) -> Dict:
        """
        Record purchase in Firebase and credit user account

        Args:
            user_id: User ID
            package: Package data
            payment_response: Nedarim Plus payment response

        Returns:
            {'success': bool, 'error': str}
        """
        logger.info(f"Recording purchase for user {user_id}")

        try:
            # Create purchase record
            purchase_data = {
                'userId': user_id,
                'packageId': package.get('id'),
                'packageName': package.get('name'),
                'minutes': package.get('minutes'),
                'prints': package.get('prints'),
                'amount': payment_response.get('Amount'),
                'transactionId': payment_response.get('TransactionId'),
                'transactionType': payment_response.get('TransactionType'),
                'creditCardNumber': payment_response.get('CreditCardNumber', '****'),
                'timestamp': datetime.now().isoformat(),
                'status': 'completed'
            }

            # Generate purchase ID
            import requests
            response = requests.post(
                f"{self.firebase.database_url}/purchases/{user_id}.json",
                params={'auth': self.firebase.id_token},
                json=purchase_data
            )

            if response.status_code != 200:
                logger.error(f"Failed to record purchase: {response.text}")
                return {
                    'success': False,
                    'error': 'Failed to record purchase'
                }

            purchase_id = response.json()['name']
            logger.info(f"Purchase recorded: {purchase_id}")

            # Credit user account
            credit_result = self.credit_user_account(user_id, package)

            if not credit_result.get('success'):
                return credit_result

            return {
                'success': True,
                'purchase_id': purchase_id,
                'new_time': credit_result['new_time'],
                'new_prints': credit_result['new_prints']
            }

        except Exception as e:
            logger.exception("Purchase recording failed")
            return {
                'success': False,
                'error': str(e)
            }

    def credit_user_account(self, user_id: str, package: Dict) -> Dict:
        """
        Add time and prints to user account
        """
        logger.info(f"Crediting user account: {user_id}")

        # Get current user data
        user_result = self.firebase.db_get(f'users/{user_id}')

        if not user_result.get('success'):
            return {
                'success': False,
                'error': 'Failed to get user data'
            }

        user_data = user_result.get('data', {})

        # Calculate new values
        current_time = user_data.get('remainingTime', 0)
        current_prints = user_data.get('remainingPrints', 0)

        new_time = current_time + (package.get('minutes', 0) * 60)  # Convert to seconds
        new_prints = current_prints + package.get('prints', 0)

        # Update user
        update_result = self.firebase.db_update(f'users/{user_id}', {
            'remainingTime': new_time,
            'remainingPrints': new_prints,
            'updatedAt': datetime.now().isoformat()
        })

        if not update_result.get('success'):
            return {
                'success': False,
                'error': 'Failed to update user balance'
            }

        logger.info(f"User credited: +{package.get('minutes')}min, +{package.get('prints')} prints")

        return {
            'success': True,
            'new_time': new_time,
            'new_prints': new_prints
        }