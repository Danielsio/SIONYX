import requests
import json
from typing import Dict, Optional
from datetime import datetime, timedelta


class FirebaseClient:
    def __init__(self, config):
        self.api_key = config.get('FIREBASE_API_KEY')
        self.project_id = config.get('FIREBASE_PROJECT_ID')
        self.auth_url = "https://identitytoolkit.googleapis.com/v1/accounts"
        self.firestore_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents"

        self.id_token = None
        self.refresh_token = None
        self.token_expiry = None

    def sign_in_with_phone(self, phone: str, password: str) -> Dict:
        """
        Note: Firebase REST API doesn't directly support phone auth.
        You'll need to use Firebase Authentication with custom token
        or implement phone verification via Cloud Functions.

        For simplicity, this example uses email/password.
        In production, call a Cloud Function that handles phone verification.
        """
        url = f"{self.auth_url}:signInWithPassword?key={self.api_key}"
        payload = {
            "email": f"{phone}@sionyx.app",  # Convert phone to email format
            "password": password,
            "returnSecureToken": True
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        self.id_token = data['idToken']
        self.refresh_token = data['refreshToken']
        self.token_expiry = datetime.now() + timedelta(seconds=int(data['expiresIn']))

        return {
            'uid': data['localId'],
            'id_token': self.id_token,
            'refresh_token': self.refresh_token
        }

    def register_user(self, phone: str, password: str, user_data: Dict) -> Dict:
        """Register new user via Cloud Function"""
        url = f"https://us-central1-{self.project_id}.cloudfunctions.net/registerUser"
        payload = {
            'phone': phone,
            'password': password,
            'firstName': user_data['first_name'],
            'lastName': user_data['last_name'],
            'email': user_data.get('email')
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def refresh_id_token(self) -> str:
        """Refresh the ID token using refresh token"""
        if not self.refresh_token:
            raise ValueError("No refresh token available")

        url = f"https://securetoken.googleapis.com/v1/token?key={self.api_key}"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        self.id_token = data['id_token']
        self.refresh_token = data['refresh_token']
        self.token_expiry = datetime.now() + timedelta(seconds=int(data['expires_in']))

        return self.id_token

    def ensure_valid_token(self):
        """Ensure ID token is valid, refresh if needed"""
        if not self.id_token or datetime.now() >= self.token_expiry:
            self.refresh_id_token()

    def get_user_data(self, uid: str) -> Dict:
        """Fetch user data from Firestore"""
        self.ensure_valid_token()

        url = f"{self.firestore_url}/users/{uid}"
        headers = {"Authorization": f"Bearer {self.id_token}"}

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return self._parse_firestore_document(response.json())

    def call_function(self, function_name: str, data: Dict) -> Dict:
        """Call a Firebase Cloud Function"""
        self.ensure_valid_token()

        url = f"https://us-central1-{self.project_id}.cloudfunctions.net/{function_name}"
        headers = {
            "Authorization": f"Bearer {self.id_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        return response.json()

    def update_user_field(self, uid: str, field: str, value) -> None:
        """Update a specific field in user document"""
        self.ensure_valid_token()

        url = f"{self.firestore_url}/users/{uid}"
        headers = {"Authorization": f"Bearer {self.id_token}"}

        payload = {
            "fields": {
                field: self._to_firestore_value(value),
                "updatedAt": {"timestampValue": datetime.utcnow().isoformat() + "Z"}
            }
        }

        response = requests.patch(url, headers=headers, json=payload, params={"updateMask.fieldPaths": field})
        response.raise_for_status()

    @staticmethod
    def _parse_firestore_document(doc: Dict) -> Dict:
        """Parse Firestore document format to Python dict"""
        if 'fields' not in doc:
            return {}

        result = {}
        for key, value in doc['fields'].items():
            if 'stringValue' in value:
                result[key] = value['stringValue']
            elif 'integerValue' in value:
                result[key] = int(value['integerValue'])
            elif 'booleanValue' in value:
                result[key] = value['booleanValue']
            elif 'timestampValue' in value:
                result[key] = datetime.fromisoformat(value['timestampValue'].replace('Z', '+00:00'))

        return result

    @staticmethod
    def _to_firestore_value(value):
        """Convert Python value to Firestore format"""
        if isinstance(value, str):
            return {"stringValue": value}
        elif isinstance(value, int):
            return {"integerValue": str(value)}
        elif isinstance(value, bool):
            return {"booleanValue": value}
        elif isinstance(value, datetime):
            return {"timestampValue": value.isoformat() + "Z"}
        else:
            return {"stringValue": str(value)}