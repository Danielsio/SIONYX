"""
Firebase Configuration

Loads Firebase configuration from:
- Windows Registry (production/frozen mode)
- .env file (development mode)
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv

from utils.registry_config import get_all_config, is_production


class FirebaseConfig:
    """Firebase configuration"""

    def __init__(self):
        if is_production():
            self._load_from_registry()
        else:
            self._load_from_env()

        self._validate()

    def _load_from_registry(self):
        """Load config from Windows Registry (production mode)"""
        config = get_all_config()

        self.api_key = config["api_key"]
        self.auth_domain = config["auth_domain"]
        self.database_url = config["database_url"]
        self.project_id = config["project_id"]
        self.org_id = config["org_id"]

    def _load_from_env(self):
        """Load config from .env file (development mode)"""
        # sionyx-kiosk/src/utils/firebase_config.py -> go up to repo root
        app_root = Path(__file__).parent.parent.parent  # sionyx-kiosk/
        repo_root = app_root.parent  # repo root

        # Try repo root first, then app root for backwards compatibility
        env_path = repo_root / ".env"
        if not env_path.exists():
            env_path = app_root / ".env"

        load_dotenv(dotenv_path=env_path)

        self.api_key = os.getenv("FIREBASE_API_KEY")
        self.auth_domain = os.getenv("FIREBASE_AUTH_DOMAIN")
        self.database_url = os.getenv("FIREBASE_DATABASE_URL")
        self.project_id = os.getenv("FIREBASE_PROJECT_ID")
        self.org_id = os.getenv("ORG_ID")

    def _validate(self):
        """Validate required config"""
        source = "registry" if is_production() else ".env"

        if not self.api_key:
            raise ValueError(f"FIREBASE_API_KEY missing in {source}")
        if not self.database_url:
            raise ValueError(f"FIREBASE_DATABASE_URL missing in {source}")
        if not self.project_id:
            raise ValueError(f"FIREBASE_PROJECT_ID missing in {source}")
        if not self.org_id:
            raise ValueError(
                f"ORG_ID missing in {source}\n"
                "This identifies your organization in the database.\n"
                "Example: ORG_ID=myorg"
            )

        # Validate org_id format (alphanumeric, lowercase, hyphens)
        if not re.match(r"^[a-z0-9-]+$", self.org_id):
            raise ValueError(
                f"Invalid ORG_ID: '{self.org_id}'\n"
                "Must contain only lowercase letters, numbers, and hyphens.\n"
                "Example: myorg, tech-lab, university-cs"
            )

    @property
    def auth_url(self):
        """Firebase Auth REST API URL"""
        return "https://identitytoolkit.googleapis.com/v1/accounts"


# Global instance - created lazily when needed
firebase_config = None


def get_firebase_config():
    """Get Firebase configuration instance (lazy loading)"""
    global firebase_config
    if firebase_config is None:
        firebase_config = FirebaseConfig()
    return firebase_config
