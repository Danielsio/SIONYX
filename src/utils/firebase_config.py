"""
Firebase Configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class FirebaseConfig:
    """Firebase configuration"""

    def __init__(self):
        self.api_key = os.getenv('FIREBASE_API_KEY')
        self.auth_domain = os.getenv('FIREBASE_AUTH_DOMAIN')
        self.database_url = os.getenv('FIREBASE_DATABASE_URL')
        self.project_id = os.getenv('FIREBASE_PROJECT_ID')

        self._validate()

    def _validate(self):
        """Validate required config"""
        if not self.api_key:
            raise ValueError("FIREBASE_API_KEY missing in .env")
        if not self.database_url:
            raise ValueError("FIREBASE_DATABASE_URL missing in .env")
        if not self.project_id:
            raise ValueError("FIREBASE_PROJECT_ID missing in .env")

    @property
    def auth_url(self):
        """Firebase Auth REST API URL"""
        return "https://identitytoolkit.googleapis.com/v1/accounts"


# Global instance
firebase_config = FirebaseConfig()