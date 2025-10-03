"""
Authentication Service - Firebase Realtime Database
"""

from typing import Dict, Optional
from datetime import datetime

from services.firebase_client import FirebaseClient
from database.local_db import LocalDatabase
from utils.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Authentication service using Firebase"""

    def __init__(self, config=None):
        self.config = config
        self.firebase = FirebaseClient()
        self.local_db = LocalDatabase()
        self.current_user = None
        logger.info("Auth service initialized")

    def is_logged_in(self) -> bool:
        """Check if user is already logged in"""
        stored_token = self.local_db.get_stored_token()

        if not stored_token:
            return False

        # Try to refresh token
        result = self.firebase.refresh_token_request(stored_token)

        if result.get('success'):
            # Load user data from Realtime Database
            user_result = self.firebase.db_get(f'users/{self.firebase.user_id}')

            if user_result.get('success') and user_result.get('data'):
                self.current_user = user_result['data']
                self.current_user['uid'] = self.firebase.user_id
                logger.info("User auto-logged in")
                return True

        return False

    def login(self, phone: str, password: str) -> Dict:
        """
        Login with phone and password
        Phone is converted to email internally
        """
        logger.info(f"Login attempt for phone: {phone}")

        # Convert phone to email format
        email = self._phone_to_email(phone)

        # Sign in with Firebase Auth
        result = self.firebase.sign_in(email, password)

        if not result.get('success'):
            logger.warning(f"Login failed for {phone}")
            return result

        uid = result['uid']

        # Get user data from Realtime Database
        user_result = self.firebase.db_get(f'users/{uid}')

        if not user_result.get('success') or not user_result.get('data'):
            logger.error(f"User data not found for {uid}")
            return {
                'success': False,
                'error': 'User data not found'
            }

        self.current_user = user_result['data']
        self.current_user['uid'] = uid

        # Store credentials locally (encrypted)
        self.local_db.store_credentials(
            uid=uid,
            phone=phone,
            refresh_token=result['refresh_token'],
            user_data=self.current_user
        )

        logger.info(f"Login successful for {phone}")
        return {
            'success': True,
            'user': self.current_user
        }

    def register(self, phone: str, password: str, first_name: str,
                 last_name: str, email: str = '') -> Dict:
        """
        Register new user
        """
        logger.info(f"Registration attempt for phone: {phone}")

        # Validate inputs
        if len(password) < 6:
            return {
                'success': False,
                'error': 'Password must be at least 6 characters'
            }

        # Convert phone to email format
        firebase_email = self._phone_to_email(phone)

        # Sign up with Firebase Auth
        result = self.firebase.sign_up(firebase_email, password)

        if not result.get('success'):
            logger.warning(f"Registration failed for {phone}")
            return result

        uid = result['uid']

        # Create user document in Realtime Database
        user_data = {
            'firstName': first_name,
            'lastName': last_name,
            'phoneNumber': phone,
            'email': email if email else '',
            'remainingTime': 0,  # Start with 0 seconds
            'remainingPrints': 0,  # Start with 0 prints
            'isActive': True,
            'createdAt': datetime.now().isoformat(),
            'updatedAt': datetime.now().isoformat()
        }

        # Save to database
        db_result = self.firebase.db_set(f'users/{uid}', user_data)

        if not db_result.get('success'):
            logger.error(f"Failed to create user data for {uid}")
            return {
                'success': False,
                'error': 'Failed to create user profile'
            }

        self.current_user = user_data
        self.current_user['uid'] = uid

        # Store credentials locally
        self.local_db.store_credentials(
            uid=uid,
            phone=phone,
            refresh_token=result['refresh_token'],
            user_data=user_data
        )

        logger.info(f"Registration successful for {phone}")
        return {
            'success': True,
            'user': self.current_user
        }

    def logout(self):
        """Logout current user"""
        if self.current_user:
            logger.info(f"User logged out: {self.current_user.get('uid')}")

        self.firebase.id_token = None
        self.firebase.refresh_token = None
        self.firebase.user_id = None
        self.local_db.clear_tokens()
        self.current_user = None

    def get_current_user(self) -> Optional[Dict]:
        """Get current logged in user data"""
        return self.current_user

    def update_user_data(self, updates: Dict) -> Dict:
        """
        Update current user's data in database
        Example: {'remainingTime': 3600, 'remainingPrints': 50}
        """
        if not self.current_user:
            return {
                'success': False,
                'error': 'No user logged in'
            }

        uid = self.current_user['uid']

        # Add timestamp
        updates['updatedAt'] = datetime.now().isoformat()

        # Update in database
        result = self.firebase.db_update(f'users/{uid}', updates)

        if result.get('success'):
            # Update local cache
            self.current_user.update(updates)
            logger.info(f"User data updated for {uid}")

        return result

    @staticmethod
    def _phone_to_email(phone: str) -> str:
        """
        Convert phone number to email format for Firebase
        Example: '1234567890' -> '1234567890@sionyx.app'
        """
        # Remove all non-digit characters
        clean_phone = ''.join(filter(str.isdigit, phone))
        return f"{clean_phone}@sionyx.app"