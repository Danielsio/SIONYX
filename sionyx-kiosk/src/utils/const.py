"""
Global constants for application branding and configuration.
"""

import os
import sys
from pathlib import Path

# Application display name (brand)
APP_NAME = "SIONYX"

# Security constants
ADMIN_EXIT_HOTKEY_DEFAULT = "ctrl+alt+space"

# Default fallback password (only used if neither registry nor .env provides one)
_DEFAULT_ADMIN_PASSWORD = "sionyx2025"


def get_admin_exit_password() -> str:
    """
    Load admin exit password from configuration.

    Priority:
      1. Windows Registry (production builds)
      2. .env file / environment variable (development)
      3. Fallback default
    """
    # Production: read from registry
    if getattr(sys, "frozen", False):
        from utils.registry_config import read_registry_value

        password = read_registry_value("AdminExitPassword")
        if password:
            return password

    # Development: read from environment
    password = os.environ.get("ADMIN_EXIT_PASSWORD")
    if password:
        return password

    # Try loading from .env if not already loaded
    try:
        from dotenv import load_dotenv

        app_root = Path(__file__).parent.parent.parent
        repo_root = app_root.parent
        env_path = repo_root / ".env"
        if not env_path.exists():
            env_path = app_root / ".env"
        load_dotenv(dotenv_path=env_path, override=False)
        password = os.environ.get("ADMIN_EXIT_PASSWORD")
        if password:
            return password
    except ImportError:
        pass

    return _DEFAULT_ADMIN_PASSWORD


# Lazy-loaded password (computed on first access)
ADMIN_EXIT_PASSWORD = get_admin_exit_password()
