"""
Authentication Service - Mock Version
We'll replace this with real Firebase later
"""

import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Mock authentication service"""

    def __init__(self, config=None):
        self.config = config
        self.current_user = None
        logger.info("Auth service initialized (mock mode)")

    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        # For now, always return False to show login screen
        return False

    def login(self, phone: str, password: str) -> dict:
        """Mock login - will be replaced with Firebase"""
        logger.info(f"Mock login attempt for: {phone}")

        # Mock validation
        if len(phone) < 10:
            return {
                'success': False,
                'error': 'Invalid phone number'
            }

        if len(password) < 6:
            return {
                'success': False,
                'error': 'Password must be at least 6 characters'
            }

        # Mock success
        self.current_user = {
            'uid': 'mock_user_123',
            'phone': phone,
            'firstName': 'Test',
            'lastName': 'User'
        }

        return {
            'success': True,
            'user': self.current_user
        }

    def register(self, phone: str, password: str, first_name: str,
                 last_name: str, email: str = '') -> dict:
        """Mock registration - will be replaced with Firebase"""
        logger.info(f"Mock registration attempt for: {phone}")

        # Mock validation
        if len(phone) < 10:
            return {
                'success': False,
                'error': 'Invalid phone number'
            }

        if len(password) < 6:
            return {
                'success': False,
                'error': 'Password must be at least 6 characters'
            }

        if not first_name or not last_name:
            return {
                'success': False,
                'error': 'First name and last name are required'
            }

        # Mock success
        self.current_user = {
            'uid': 'mock_new_user_456',
            'phone': phone,
            'firstName': first_name,
            'lastName': last_name,
            'email': email
        }

        return {
            'success': True,
            'user': self.current_user
        }

    def logout(self):
        """Logout current user"""
        self.current_user = None
        logger.info("User logged out")