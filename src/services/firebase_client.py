"""
Firebase Client - Realtime Database + Authentication
"""

import requests
import json
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

from utils.firebase_config import firebase_config

logger = logging.getLogger(__name__)


class FirebaseClient:
    """Firebase REST API client for Realtime Database"""

    def __init__(self):
        self.api_key = firebase_config.api_key
        self.database_url = firebase_config.database_url
        self.auth_url = firebase_config.auth_url

        # Auth state
        self.id_token = None
        self.refresh_token = None
        self.token_expiry = None
        self.user_id = None

        logger.info("Firebase client initialized")

    # ==================== AUTHENTICATION ====================

    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign up new user
        Email will be in format: phone@sionyx.app
        """
        url = f"{self.auth_url}:signUp?key={self.api_key}"

        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            self._store_auth_data(data)

            logger.info(f"User signed up: {self.user_id}")
            return {
                'success': True,
                'uid': self.user_id,
                'id_token': self.id_token,
                'refresh_token': self.refresh_token
            }

        except requests.exceptions.RequestException as e:
            error_msg = self._parse_error(e)
            logger.error(f"Sign up failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in existing user"""
        url = f"{self.auth_url}:signInWithPassword?key={self.api_key}"

        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        try:
            print(f"DEBUG: Signing in with email: {email}")  # DEBUG
            response = requests.post(url, json=payload, timeout=10)

            print(f"DEBUG: Response status: {response.status_code}")  # DEBUG
            print(f"DEBUG: Response body: {response.text}")  # DEBUG

            response.raise_for_status()

            data = response.json()
            self._store_auth_data(data)

            logger.info(f"User signed in: {self.user_id}")
            return {
                'success': True,
                'uid': self.user_id,
                'id_token': self.id_token,
                'refresh_token': self.refresh_token
            }

        except requests.exceptions.RequestException as e:
            error_msg = self._parse_error(e)
            print(f"DEBUG: Sign in error: {error_msg}")  # DEBUG
            logger.error(f"Sign in failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

    def refresh_token_request(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh ID token"""
        url = f"https://securetoken.googleapis.com/v1/token?key={self.api_key}"

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()
            self.id_token = data['id_token']
            self.refresh_token = data['refresh_token']
            self.user_id = data['user_id']
            self.token_expiry = datetime.now() + timedelta(seconds=int(data['expires_in']))

            logger.info("Token refreshed")
            return {
                'success': True,
                'id_token': self.id_token,
                'refresh_token': self.refresh_token
            }

        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _store_auth_data(self, data: Dict):
        """Store auth data from Firebase response"""
        self.id_token = data['idToken']
        self.refresh_token = data['refreshToken']
        self.user_id = data['localId']
        self.token_expiry = datetime.now() + timedelta(seconds=int(data['expiresIn']))

    def ensure_valid_token(self) -> bool:
        """Ensure token is valid, refresh if needed"""
        if not self.id_token or not self.refresh_token:
            return False

        # Refresh if expiring in next 5 minutes
        if datetime.now() >= self.token_expiry - timedelta(minutes=5):
            result = self.refresh_token_request(self.refresh_token)
            return result.get('success', False)

        return True

    # ==================== REALTIME DATABASE ====================

    def db_get(self, path: str) -> Dict[str, Any]:
        """Get data from Realtime Database"""
        if not self.ensure_valid_token():
            print("DEBUG: Token validation failed in db_get")  # DEBUG
            return {'success': False, 'error': 'Not authenticated'}

        url = f"{self.database_url}/{path}.json"
        params = {'auth': self.id_token}

        print(f"DEBUG: DB GET URL: {url}")  # DEBUG
        print(f"DEBUG: Token exists: {bool(self.id_token)}")  # DEBUG

        try:
            response = requests.get(url, params=params, timeout=10)

            print(f"DEBUG: DB GET status: {response.status_code}")  # DEBUG
            print(f"DEBUG: DB GET response: {response.text}")  # DEBUG

            response.raise_for_status()

            data = response.json()
            logger.info(f"DB GET: {path}")

            return {
                'success': True,
                'data': data
            }

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            print(f"DEBUG: DB GET error: {error_msg}")  # DEBUG
            logger.error(f"DB GET failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

    def db_set(self, path: str, data: Any) -> Dict[str, Any]:
        """
        Set data in Realtime Database (overwrites)
        Path example: 'users/user123'
        """
        if not self.ensure_valid_token():
            return {'success': False, 'error': 'Not authenticated'}

        url = f"{self.database_url}/{path}.json"
        params = {'auth': self.id_token}

        try:
            response = requests.put(url, params=params, json=data, timeout=10)
            response.raise_for_status()

            logger.info(f"DB SET: {path}")
            return {
                'success': True,
                'data': response.json()
            }

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            logger.error(f"DB SET failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

    def db_update(self, path: str, data: Dict) -> Dict[str, Any]:
        """
        Update data in Realtime Database (merge, don't overwrite)
        Path example: 'users/user123'
        """
        if not self.ensure_valid_token():
            return {'success': False, 'error': 'Not authenticated'}

        url = f"{self.database_url}/{path}.json"
        params = {'auth': self.id_token}

        try:
            response = requests.patch(url, params=params, json=data, timeout=10)
            response.raise_for_status()

            logger.info(f"DB UPDATE: {path}")
            return {
                'success': True,
                'data': response.json()
            }

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            logger.error(f"DB UPDATE failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

    def db_delete(self, path: str) -> Dict[str, Any]:
        """
        Delete data from Realtime Database
        """
        if not self.ensure_valid_token():
            return {'success': False, 'error': 'Not authenticated'}

        url = f"{self.database_url}/{path}.json"
        params = {'auth': self.id_token}

        try:
            response = requests.delete(url, params=params, timeout=10)
            response.raise_for_status()

            logger.info(f"DB DELETE: {path}")
            return {'success': True}

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            logger.error(f"DB DELETE failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }

    # ==================== HELPER METHODS ====================

    @staticmethod
    def _parse_error(exception: Exception) -> str:
        """Parse Firebase error to user-friendly message"""
        if hasattr(exception, 'response') and exception.response is not None:
            try:
                error_data = exception.response.json()
                if 'error' in error_data:
                    message = error_data['error'].get('message', '')

                    # User-friendly error messages
                    if 'EMAIL_EXISTS' in message:
                        return 'This phone number is already registered'
                    elif 'INVALID_PASSWORD' in message or 'EMAIL_NOT_FOUND' in message:
                        return 'Invalid phone number or password'
                    elif 'WEAK_PASSWORD' in message:
                        return 'Password must be at least 6 characters'
                    elif 'TOO_MANY_ATTEMPTS' in message:
                        return 'Too many attempts. Please try again later'

                    return message
            except:
                pass

        return str(exception)