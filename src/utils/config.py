"""
Configuration Management
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration"""

    def __init__(self):
        self.app_name = "Sionyx"
        self.app_version = "1.0.0"

        # Firebase config (will use later)
        self.firebase_api_key = os.getenv('FIREBASE_API_KEY', '')
        self.firebase_project_id = os.getenv('FIREBASE_PROJECT_ID', '')

        # App settings
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

    def get(self, key: str, default=None):
        """Get configuration value"""
        return getattr(self, key, default)