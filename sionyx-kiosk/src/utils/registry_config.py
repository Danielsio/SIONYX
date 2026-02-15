"""
Windows Registry Configuration Reader

Reads SIONYX configuration from Windows Registry for production builds.
Development builds continue to use .env files.
"""

import sys


# Only import winreg on Windows
try:
    import winreg
except ImportError:
    winreg = None  # type: ignore

REGISTRY_KEY = r"SOFTWARE\SIONYX"


def is_production() -> bool:
    """Check if running as PyInstaller executable (frozen mode)"""
    return getattr(sys, "frozen", False)


def read_registry_value(name: str, default: str | None = None) -> str | None:
    """
    Read a value from SIONYX registry key.

    Args:
        name: The registry value name to read
        default: Default value if not found

    Returns:
        The registry value or default if not found
    """
    if winreg is None:
        return default

    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRY_KEY)
        value, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return value
    except (OSError, FileNotFoundError):
        return default


def get_all_config() -> dict:
    """
    Read all SIONYX configuration from registry.

    Returns:
        Dictionary with all config values (some may be None if not set)
    """
    return {
        # Required values
        "org_id": read_registry_value("OrgId"),
        "api_key": read_registry_value("FirebaseApiKey"),
        "auth_domain": read_registry_value("FirebaseAuthDomain"),
        "project_id": read_registry_value("FirebaseProjectId"),
        "database_url": read_registry_value("FirebaseDatabaseUrl"),
        # Optional values
        "storage_bucket": read_registry_value("FirebaseStorageBucket"),
        "messaging_sender_id": read_registry_value("FirebaseMessagingSenderId"),
        "app_id": read_registry_value("FirebaseAppId"),
        "measurement_id": read_registry_value("FirebaseMeasurementId"),
    }


def registry_config_exists() -> bool:
    """
    Check if SIONYX registry key exists with required values.

    Returns:
        True if registry key exists and has OrgId set
    """
    if winreg is None:
        return False

    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRY_KEY)
        # Check if at least OrgId exists
        winreg.QueryValueEx(key, "OrgId")
        winreg.CloseKey(key)
        return True
    except (OSError, FileNotFoundError):
        return False
