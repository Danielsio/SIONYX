"""
Firebase Configuration
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


class FirebaseConfig:
    """Firebase configuration"""

    def __init__(self):
        # Load .env file when FirebaseConfig is instantiated
        # Handle PyInstaller path resolution
        if getattr(sys, "frozen", False):
            # Running as PyInstaller executable - look in executable directory
            base_path = Path(sys.executable).parent
            env_path = base_path / ".env"
        else:
            # Running as script - look in repo root (parent of sionyx-desktop)
            # sionyx-desktop/src/utils/firebase_config.py -> go up 4 levels to repo root
            app_root = Path(__file__).parent.parent.parent  # sionyx-desktop/
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

        # MULTI-TENANCY: Organization ID for data isolation
        self.org_id = os.getenv("ORG_ID")

        self._validate()

    def _validate(self):
        """Validate required config"""
        if not self.api_key:
            raise ValueError("FIREBASE_API_KEY missing in .env")
        if not self.database_url:
            raise ValueError("FIREBASE_DATABASE_URL missing in .env")
        if not self.project_id:
            raise ValueError("FIREBASE_PROJECT_ID missing in .env")
        if not self.org_id:
            raise ValueError(
                "ORG_ID missing in .env\n"
                "This identifies your organization in the database.\n"
                "Example: ORG_ID=myorg"
            )

        # Validate org_id format (alphanumeric, lowercase, hyphens)
        import re

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
