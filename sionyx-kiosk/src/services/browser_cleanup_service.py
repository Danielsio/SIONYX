"""
Browser Cleanup Service
Clears browser cookies and session data on session end.

This prevents the next user from accessing the previous user's
logged-in accounts (Gmail, Facebook, etc.)
"""

import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from utils.logger import get_logger

# Hide console window on Windows when spawning subprocesses (tasklist, taskkill)
_SUBPROCESS_FLAGS = (
    subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
)


logger = get_logger(__name__)


class BrowserCleanupService:
    """
    Service to clear browser cookies and session data.

    Supports:
    - Google Chrome
    - Microsoft Edge
    - Mozilla Firefox

    Security Note:
    This is essential for kiosk environments where multiple users
    share the same computer. Without cleanup, a user's logged-in
    sessions would persist for the next user.
    """

    # Browser data directories (relative to user profile)
    CHROME_PATHS = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "User Data",
    ]

    EDGE_PATHS = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Edge" / "User Data",
    ]

    FIREFOX_PATHS = [
        Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox" / "Profiles",
    ]

    # Files to delete (sensitive session data)
    CHROMIUM_FILES_TO_DELETE = [
        "Cookies",
        "Cookies-journal",
        "Login Data",
        "Login Data-journal",
        "Web Data",
        "Web Data-journal",
        "History",
        "History-journal",
        "Sessions",
        "Current Session",
        "Current Tabs",
        "Last Session",
        "Last Tabs",
    ]

    FIREFOX_FILES_TO_DELETE = [
        "cookies.sqlite",
        "cookies.sqlite-wal",
        "cookies.sqlite-shm",
        "logins.json",
        "key4.db",
        "signons.sqlite",
        "sessionstore.jsonlz4",
        "sessionstore-backups",
    ]

    def __init__(self):
        """Initialize the browser cleanup service."""
        self._cleanup_results: Dict[str, bool] = {}

    def cleanup_all_browsers(self) -> Dict[str, any]:
        """
        Clean up all supported browsers.

        Returns:
            Dict with success status and details for each browser
        """
        logger.info("Starting browser cleanup for all browsers")

        results = {
            "success": True,
            "chrome": self._cleanup_chrome(),
            "edge": self._cleanup_edge(),
            "firefox": self._cleanup_firefox(),
            "errors": [],
        }

        # Check if any browser cleanup failed
        for browser, result in results.items():
            if browser not in ("success", "errors") and not result.get("success", True):
                results["errors"].append(f"{browser}: {result.get('error', 'Unknown')}")

        if results["errors"]:
            results["success"] = False
            logger.warning(f"Browser cleanup completed with errors: {results['errors']}")
        else:
            logger.info("Browser cleanup completed successfully")

        return results

    def _cleanup_chrome(self) -> Dict[str, any]:
        """Clean up Google Chrome data."""
        return self._cleanup_chromium_browser("Chrome", self.CHROME_PATHS)

    def _cleanup_edge(self) -> Dict[str, any]:
        """Clean up Microsoft Edge data."""
        return self._cleanup_chromium_browser("Edge", self.EDGE_PATHS)

    def _cleanup_chromium_browser(
        self, browser_name: str, base_paths: List[Path]
    ) -> Dict[str, any]:
        """
        Clean up a Chromium-based browser (Chrome, Edge).

        Args:
            browser_name: Name of the browser for logging
            base_paths: List of possible base paths for user data

        Returns:
            Dict with success status and files deleted count
        """
        files_deleted = 0
        errors = []

        for base_path in base_paths:
            if not base_path.exists():
                logger.debug(f"{browser_name}: Base path not found: {base_path}")
                continue

            # Find all profile directories (Default, Profile 1, Profile 2, etc.)
            profile_dirs = self._find_chromium_profiles(base_path)

            for profile_dir in profile_dirs:
                for file_name in self.CHROMIUM_FILES_TO_DELETE:
                    file_path = profile_dir / file_name
                    if file_path.exists():
                        try:
                            if file_path.is_dir():
                                shutil.rmtree(file_path)
                            else:
                                file_path.unlink()
                            files_deleted += 1
                            logger.debug(f"{browser_name}: Deleted {file_path}")
                        except PermissionError as e:
                            # Browser might be running
                            errors.append(f"Permission denied: {file_path}")
                            logger.warning(
                                f"{browser_name}: Cannot delete {file_path} "
                                f"(browser may be running): {e}"
                            )
                        except Exception as e:
                            errors.append(f"Error deleting {file_path}: {e}")
                            logger.error(f"{browser_name}: Error deleting {file_path}: {e}")

        if errors:
            return {
                "success": False,
                "files_deleted": files_deleted,
                "error": "; ".join(errors[:3]),  # Limit error messages
            }

        logger.info(f"{browser_name}: Cleanup complete, {files_deleted} files deleted")
        return {"success": True, "files_deleted": files_deleted}

    def _cleanup_firefox(self) -> Dict[str, any]:
        """Clean up Mozilla Firefox data."""
        files_deleted = 0
        errors = []

        for base_path in self.FIREFOX_PATHS:
            if not base_path.exists():
                logger.debug(f"Firefox: Profiles path not found: {base_path}")
                continue

            # Firefox profiles are named like "xxxxxxxx.default-release"
            try:
                for profile_dir in base_path.iterdir():
                    if not profile_dir.is_dir():
                        continue

                    for file_name in self.FIREFOX_FILES_TO_DELETE:
                        file_path = profile_dir / file_name
                        if file_path.exists():
                            try:
                                if file_path.is_dir():
                                    shutil.rmtree(file_path)
                                else:
                                    file_path.unlink()
                                files_deleted += 1
                                logger.debug(f"Firefox: Deleted {file_path}")
                            except PermissionError as e:
                                errors.append(f"Permission denied: {file_path}")
                                logger.warning(
                                    f"Firefox: Cannot delete {file_path} "
                                    f"(browser may be running): {e}"
                                )
                            except Exception as e:
                                errors.append(f"Error deleting {file_path}: {e}")
                                logger.error(f"Firefox: Error deleting {file_path}: {e}")
            except Exception as e:
                errors.append(f"Error accessing profiles: {e}")
                logger.error(f"Firefox: Error accessing profiles: {e}")

        if errors:
            return {
                "success": False,
                "files_deleted": files_deleted,
                "error": "; ".join(errors[:3]),
            }

        logger.info(f"Firefox: Cleanup complete, {files_deleted} files deleted")
        return {"success": True, "files_deleted": files_deleted}

    def _find_chromium_profiles(self, base_path: Path) -> List[Path]:
        """
        Find all Chromium profile directories.

        Args:
            base_path: Chrome/Edge User Data directory

        Returns:
            List of profile directory paths
        """
        profiles = []

        # Default profile
        default_profile = base_path / "Default"
        if default_profile.exists():
            profiles.append(default_profile)

        # Numbered profiles (Profile 1, Profile 2, etc.)
        try:
            for item in base_path.iterdir():
                if item.is_dir() and item.name.startswith("Profile "):
                    profiles.append(item)
        except Exception as e:
            logger.debug(f"Error finding profiles in {base_path}: {e}")

        return profiles

    def is_browser_running(self, browser_name: str) -> bool:
        """
        Check if a browser is currently running.

        Args:
            browser_name: 'chrome', 'edge', or 'firefox'

        Returns:
            True if the browser process is running
        """
        process_names = {
            "chrome": ["chrome.exe"],
            "edge": ["msedge.exe"],
            "firefox": ["firefox.exe"],
        }

        names = process_names.get(browser_name.lower(), [])

        try:
            result = subprocess.run(
                ["tasklist", "/FO", "CSV"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=_SUBPROCESS_FLAGS,
            )
            output = result.stdout.lower()
            return any(name.lower() in output for name in names)
        except Exception as e:
            logger.debug(f"Error checking if {browser_name} is running: {e}")
            return False

    def close_browsers(self) -> Dict[str, bool]:
        """
        Attempt to close all browsers gracefully.

        Returns:
            Dict with browser name -> success status
        """
        results = {}
        browsers = {
            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "firefox": "firefox.exe",
        }

        for name, process in browsers.items():
            if self.is_browser_running(name):
                try:
                    # Use taskkill to close gracefully
                    subprocess.run(
                        ["taskkill", "/IM", process, "/F"],
                        capture_output=True,
                        timeout=10,
                        creationflags=_SUBPROCESS_FLAGS,
                    )
                    results[name] = True
                    logger.info(f"Closed {name}")
                except Exception as e:
                    results[name] = False
                    logger.warning(f"Failed to close {name}: {e}")
            else:
                results[name] = True  # Already closed

        return results

    def cleanup_with_browser_close(self) -> Dict[str, any]:
        """
        Close browsers first, then clean up.

        This is the recommended method for session end cleanup.

        Returns:
            Dict with success status and cleanup details
        """
        logger.info("Closing browsers before cleanup...")

        # Close browsers first
        close_results = self.close_browsers()

        # Give browsers time to close
        import time
        time.sleep(1)

        # Now clean up
        cleanup_results = self.cleanup_all_browsers()
        cleanup_results["browsers_closed"] = close_results

        return cleanup_results
