"""
Device Information Utility
Collects unique PC/computer identification data
"""

import hashlib
import platform
import socket
import uuid
from typing import Dict, Optional

from utils.logger import get_logger


logger = get_logger(__name__)


def get_device_id() -> str:
    """
    Generate a unique device ID based on hardware characteristics.
    Uses MAC address for stability, falls back to hash of computer name.
    """
    try:
        # Try to get MAC address first (most reliable)
        mac = _get_mac_address()
        if mac:
            return mac.replace(":", "").lower()

        # Fallback to computer name + platform hash
        computer_name = get_computer_name()
        platform_info = f"{platform.system()}-{platform.machine()}"
        combined = f"{computer_name}-{platform_info}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    except Exception as e:
        logger.warning(f"Failed to generate device ID: {e}")
        return str(uuid.uuid4())[:16]


def get_computer_name() -> str:
    """Get the computer name/hostname"""
    try:
        if platform.system() == "Windows":
            return platform.node() or socket.gethostname()
        return socket.gethostname()
    except Exception as e:
        logger.warning(f"Failed to get computer name: {e}")
        return "Unknown-PC"


def _get_mac_address() -> Optional[str]:
    """
    Get MAC address of the primary network interface.
    Internal function - used only for generating device ID.
    """
    try:
        mac = uuid.getnode()
        if mac != uuid.getnode():  # Check if MAC is valid
            return None
        mac_str = ":".join(
            ["{:02x}".format((mac >> ele) & 0xFF) for ele in range(0, 8 * 6, 8)][::-1]
        )
        return mac_str
    except Exception as e:
        logger.warning(f"Failed to get MAC address: {e}")
        return None


def get_computer_info() -> Dict[str, any]:
    """
    Get computer information for registration.
    Returns minimal data needed for PC identification.
    Note: isActive is derived from currentUserId (not stored separately)
    """
    try:
        return {
            "computerName": get_computer_name(),
            "deviceId": get_device_id(),
        }
    except Exception as e:
        logger.error(f"Failed to get computer info: {e}")
        return {
            "computerName": "Unknown-PC",
            "deviceId": str(uuid.uuid4())[:16],
        }
