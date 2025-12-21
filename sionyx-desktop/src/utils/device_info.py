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
    Generate a unique device ID based on hardware characteristics
    Falls back to simpler methods if hardware info is unavailable
    """
    try:
        # Try to get MAC address first (most reliable)
        mac = get_mac_address()
        if mac:
            return mac.replace(":", "").lower()

        # Fallback to computer name + platform
        computer_name = get_computer_name()
        platform_info = f"{platform.system()}-{platform.machine()}"
        combined = f"{computer_name}-{platform_info}"

        # Create hash for consistency (using SHA-256 for better security)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    except Exception as e:
        logger.warning(f"Failed to generate device ID: {e}")
        # Ultimate fallback
        return str(uuid.uuid4())[:16]


def get_computer_name() -> str:
    """Get the computer name/hostname"""
    try:
        # Windows
        if platform.system() == "Windows":
            return platform.node() or socket.gethostname()

        # Linux/Mac
        return socket.gethostname()

    except Exception as e:
        logger.warning(f"Failed to get computer name: {e}")
        return "unknown-pc"


def get_mac_address() -> Optional[str]:
    """Get MAC address of the primary network interface"""
    try:
        # Get MAC address using uuid.getnode()
        mac = uuid.getnode()
        if mac != uuid.getnode():  # Check if MAC is valid
            return None

        # Convert to readable format
        mac_str = ":".join(
            ["{:02x}".format((mac >> ele) & 0xFF) for ele in range(0, 8 * 6, 8)][::-1]
        )
        return mac_str

    except Exception as e:
        logger.warning(f"Failed to get MAC address: {e}")
        return None


def get_hardware_fingerprint() -> str:
    """
    Create a hardware fingerprint combining multiple system characteristics
    """
    try:
        components = []

        # Computer name
        components.append(get_computer_name())

        # Platform info
        components.append(f"{platform.system()}-{platform.machine()}")

        # MAC address
        mac = get_mac_address()
        if mac:
            components.append(mac)

        # CPU info (if available)
        try:
            cpu_info = platform.processor()
            if cpu_info and cpu_info != "":
                components.append(cpu_info)
        except Exception:
            pass

        # Combine and hash
        combined = "-".join(components)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    except Exception as e:
        logger.warning(f"Failed to create hardware fingerprint: {e}")
        return str(uuid.uuid4())


def get_os_info() -> Dict[str, str]:
    """Get detailed operating system information"""
    try:
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor() or "Unknown",
            "architecture": (
                platform.architecture()[0] if platform.architecture() else "Unknown"
            ),
        }
    except Exception as e:
        logger.warning(f"Failed to get OS info: {e}")
        return {
            "system": "Unknown",
            "release": "Unknown",
            "version": "Unknown",
            "machine": "Unknown",
            "processor": "Unknown",
            "architecture": "Unknown",
        }


def get_network_info() -> Dict[str, str]:
    """Get current network information"""
    try:
        # Get local IP address
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        return {
            "hostname": hostname,
            "local_ip": local_ip,
            "mac_address": get_mac_address() or "Unknown",
        }
    except Exception as e:
        logger.warning(f"Failed to get network info: {e}")
        return {"hostname": "Unknown", "local_ip": "Unknown", "mac_address": "Unknown"}


def get_computer_info() -> Dict[str, any]:
    """
    Get comprehensive computer information for registration
    Returns all relevant data for PC identification
    """
    try:
        computer_name = get_computer_name()
        device_id = get_device_id()
        hardware_id = get_hardware_fingerprint()

        return {
            "computerName": computer_name,
            "deviceId": device_id,
            "hardwareId": hardware_id,
            "macAddress": get_mac_address(),
            "osInfo": get_os_info(),
            "networkInfo": get_network_info(),
            "isActive": True,
        }

    except Exception as e:
        logger.error(f"Failed to get computer info: {e}")
        # Return minimal info as fallback
        return {
            "computerName": "Unknown-PC",
            "deviceId": str(uuid.uuid4())[:16],
            "hardwareId": str(uuid.uuid4()),
            "macAddress": None,
            "osInfo": {"system": "Unknown"},
            "networkInfo": {"hostname": "Unknown"},
            "isActive": True,
        }
