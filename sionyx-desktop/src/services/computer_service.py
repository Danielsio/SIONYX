"""
Computer/PC Management Service
Handles computer registration, tracking, and association with users
"""

from datetime import datetime
from typing import Dict

from services.firebase_client import FirebaseClient
from utils.device_info import get_computer_info, get_device_id
from utils.logger import get_logger


logger = get_logger(__name__)


class ComputerService:
    """Manages computer/PC registration and tracking"""

    def __init__(self, firebase_client: FirebaseClient):
        self.firebase = firebase_client

    def get_computer_id(self) -> str:
        """
        Get the unique ID of the current computer.
        Uses the device ID as the computer identifier.

        Returns:
            str: The computer/device ID
        """
        return get_device_id()

    def register_computer(
        self, computer_name: str = None, location: str = None
    ) -> Dict:
        """
        Register the current computer in the organization

        Args:
            computer_name: Optional custom name for the computer
            location: Optional location description (e.g., "Lab A", "Room 101")

        Returns:
            {'success': bool, 'computer_id': str, 'error': str}
        """
        try:
            logger.debug("Registering computer", action="computer_registration")

            # Get computer information
            computer_info = get_computer_info()

            # Use provided name or generate one
            if computer_name:
                computer_info["computerName"] = computer_name
            elif (
                not computer_info.get("computerName")
                or computer_info["computerName"] == "Unknown-PC"
            ):
                computer_info["computerName"] = (
                    f"PC-{computer_info['deviceId'][:8].upper()}"
                )

            # Add location if provided
            if location:
                computer_info["location"] = location

            # Add timestamps (currentUserId=None means not active)
            now = datetime.now().isoformat()
            computer_info.update(
                {
                    "currentUserId": None,
                    "createdAt": now,
                    "updatedAt": now,
                }
            )

            # Generate computer ID (use device ID as base)
            computer_id = computer_info["deviceId"]

            # Save to database
            result = self.firebase.db_set(f"computers/{computer_id}", computer_info)

            if not result.get("success"):
                logger.error("Failed to register computer")
                return {"success": False, "error": "Failed to register computer"}

            logger.info(
                "Computer registered successfully",
                computer_id=computer_id,
                action="computer_registration",
            )
            return {
                "success": True,
                "computer_id": computer_id,
                "computer_name": computer_info["computerName"],
            }

        except Exception as e:
            logger.error(
                "Computer registration failed",
                error=str(e),
                action="computer_registration",
            )
            return {"success": False, "error": str(e)}

    def get_computer_info(self, computer_id: str) -> Dict:
        """
        Get computer information by ID

        Args:
            computer_id: The computer ID to look up

        Returns:
            {'success': bool, 'data': dict, 'error': str}
        """
        try:
            result = self.firebase.db_get(f"computers/{computer_id}")
            return result

        except Exception as e:
            logger.error(f"Failed to get computer info: {e}")
            return {"success": False, "error": str(e)}

    def associate_user_with_computer(
        self, user_id: str, computer_id: str, is_login: bool = False
    ) -> Dict:
        """
        Associate a user with a computer (when they log in)

        Args:
            user_id: The user ID
            computer_id: The computer ID
            is_login: If True, also sets isLoggedIn to True (called during login)

        Returns:
            {'success': bool, 'error': str}
        """
        try:
            now = datetime.now().isoformat()

            # Update user record with computer association
            user_updates = {
                "currentComputerId": computer_id,
                "updatedAt": now,
            }

            # Set isLoggedIn to True if this is a login operation
            if is_login:
                user_updates["isLoggedIn"] = True

            result = self.firebase.db_update(f"users/{user_id}", user_updates)

            if result.get("success"):
                # Update computer with current user (this makes it "active")
                self.firebase.db_update(
                    f"computers/{computer_id}",
                    {
                        "currentUserId": user_id,
                        "updatedAt": now,
                    },
                )

            return result

        except Exception as e:
            logger.error(f"Failed to associate user with computer: {e}")
            return {"success": False, "error": str(e)}

    def disassociate_user_from_computer(
        self, user_id: str, computer_id: str, is_logout: bool = False
    ) -> Dict:
        """
        Disassociate a user from a computer (when they log out)

        Args:
            user_id: The user ID
            computer_id: The computer ID
            is_logout: If True, also sets isLoggedIn to False (called during logout)

        Returns:
            {'success': bool, 'error': str}
        """
        try:
            now = datetime.now().isoformat()

            # Build user updates
            user_updates = {
                "currentComputerId": None,
                "updatedAt": now,
            }

            # Set isLoggedIn to False if this is a logout operation
            if is_logout:
                user_updates["isLoggedIn"] = False

            # Clear user's current computer
            user_result = self.firebase.db_update(f"users/{user_id}", user_updates)

            # Clear computer's current user (this makes it "inactive")
            computer_result = self.firebase.db_update(
                f"computers/{computer_id}",
                {
                    "currentUserId": None,
                    "updatedAt": now,
                },
            )

            return user_result if user_result.get("success") else computer_result

        except Exception as e:
            logger.error(f"Failed to disassociate user from computer: {e}")
            return {"success": False, "error": str(e)}

    def get_all_computers(self) -> Dict:
        """
        Get all computers in the organization

        Returns:
            {'success': bool, 'data': dict, 'error': str}
        """
        try:
            result = self.firebase.db_get("computers")
            return result

        except Exception as e:
            logger.error(f"Failed to get all computers: {e}")
            return {"success": False, "error": str(e)}

    def get_computer_usage_stats(self) -> Dict:
        """
        Get computer usage statistics for admin dashboard

        Returns:
            {'success': bool, 'data': dict, 'error': str}
        """
        try:
            # Get all computers
            computers_result = self.get_all_computers()
            if not computers_result.get("success"):
                return computers_result

            computers = computers_result.get("data") or {}

            # Get all users
            users_result = self.firebase.db_get("users")
            if not users_result.get("success"):
                return users_result

            users = users_result.get("data") or {}

            # Process statistics
            stats = {
                "total_computers": len(computers),
                "active_computers": 0,
                "computers_with_users": 0,
                "computer_details": [],
            }

            for computer_id, computer_data in computers.items():
                current_user_id = computer_data.get("currentUserId")
                # Derive isActive from currentUserId
                is_active = current_user_id is not None

                if is_active:
                    stats["active_computers"] += 1
                    stats["computers_with_users"] += 1

                    # Get user info
                    user_data = users.get(current_user_id, {})
                    first_name = user_data.get("firstName", "")
                    last_name = user_data.get("lastName", "")
                    user_name = f"{first_name} {last_name}".strip()

                    stats["computer_details"].append(
                        {
                            "computerId": computer_id,
                            "computerName": computer_data.get(
                                "computerName", "Unknown"
                            ),
                            "isActive": True,
                            "currentUserId": current_user_id,
                            "currentUserName": user_name,
                        }
                    )
                else:
                    # Computer without user (not active)
                    stats["computer_details"].append(
                        {
                            "computerId": computer_id,
                            "computerName": computer_data.get(
                                "computerName", "Unknown"
                            ),
                            "isActive": False,
                            "currentUserId": None,
                            "currentUserName": None,
                        }
                    )

            return {"success": True, "data": stats}

        except Exception as e:
            logger.error(f"Failed to get computer usage stats: {e}")
            return {"success": False, "error": str(e)}
